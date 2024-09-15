from dotenv import load_dotenv
from github import Github, InputGitTreeElement, GithubException
import os
import openai
import base64
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

class CodeImprover:
    def __init__(self, repo_name):
        self.gh_token = os.getenv("GITHUB_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.repo_name = repo_name

        # Validate environment variables
        assert self.gh_token, "GITHUB_TOKEN must be set as an environment variable."
        assert self.openai_api_key, "OPENAI_API_KEY must be set as an environment variable."

        # Debugging: Check token lengths (do not print tokens)
        logging.info(f"GITHUB_TOKEN length: {len(self.gh_token)}")
        logging.info(f"OPENAI_API_KEY length: {len(self.openai_api_key)}")

        # Authenticate with GitHub
        self.g = Github(self.gh_token)
        self.repo = self.authenticate_repo()

        # Authenticate with OpenAI
        openai.api_key = self.openai_api_key

    def authenticate_repo(self):
        try:
            repo = self.g.get_repo(self.repo_name)
            logging.info(f"Authenticated to repository: {repo.full_name}")
            return repo
        except GithubException as e:
            if e.status == 401:
                logging.error("Authentication failed: Bad credentials. Please check your GITHUB_TOKEN.")
            elif e.status == 403:
                logging.error("Access forbidden: You do not have the necessary permissions.")
            elif e.status == 404:
                logging.error("Repository not found: Please check the repository name and your permissions.")
            else:
                logging.error(f"An error occurred: {e.data['message']}")
            raise


    def create_branch(self):
        default_branch = self.repo.default_branch
        new_branch_name = f'code-improvements-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        sb = self.repo.get_branch(default_branch)
        self.repo.create_git_ref(ref='refs/heads/' + new_branch_name, sha=sb.commit.sha)
        return new_branch_name, sb

    def improve_code(self, code):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that improves Python code quality. Only return the code itself, if no code found -- skip."},
                    {"role": "user", "content": f"Improve the following Python code for better readability, efficiency, and compliance with PEP8 standards:\n\n{code}"}
                ],
                temperature=0.7,
                max_tokens=1500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error during OpenAI API call: {e}")
            return None

    def process_files(self, default_branch, new_branch_name, sb):
        element_list = []
        contents = self.repo.get_contents("", ref=default_branch)
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            elif file_content.path.endswith('.py'):
                if file_content.size > 1_000_000:
                    file_content = self.repo.get_contents(file_content.path, ref=default_branch)

                decoded_content = base64.b64decode(file_content.content).decode('utf-8')
                improved_code = self.improve_code(decoded_content)

                if improved_code:
                    element = InputGitTreeElement(
                        path=file_content.path,
                        mode='100644',
                        type='blob',
                        content=improved_code
                    )
                    element_list.append(element)

        return element_list

    def commit_changes(self, element_list, new_branch_name, sb):
        if element_list:
            base_tree = self.repo.get_git_tree(sb.commit.sha)
            tree = self.repo.create_git_tree(element_list, base_tree)
            parent = self.repo.get_git_commit(sb.commit.sha)
            commit_message = 'Automated code improvements using GPT-4'
            commit = self.repo.create_git_commit(commit_message, tree, [parent])
            self.repo.get_git_ref('heads/' + new_branch_name).edit(commit.sha)

            # Create a Pull Request
            pr = self.repo.create_pull(
                title='Automated Code Improvements',
                body='This PR includes code improvements made by GPT-4.',
                head=new_branch_name,
                base=self.repo.default_branch
            )
            logging.info(f'Pull Request created: {pr.html_url}')
        else:
            logging.info('No Python files found to improve.')

    def run(self):
        new_branch_name, sb = self.create_branch()
        element_list = self.process_files(self.repo.default_branch, new_branch_name, sb)
        self.commit_changes(element_list, new_branch_name, sb)

if __name__ == "__main__":
    CodeImprover()
    # code_improver = CodeImprover('Cowgirl-AI/github_gpt_bot')
    # code_improver.run()
