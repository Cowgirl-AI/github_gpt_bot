```python
from dotenv import load_dotenv
from github import Github, InputGitTreeElement, GithubException
import os
import openai
import base64
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class CodeImprover:
    def __init__(self, repo_name):
        load_dotenv()
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.repo_name = repo_name

        # Validate environment variables
        self._validate_env_variables()

        # Authenticate with GitHub and OpenAI
        self.github = Github(self.github_token)
        self.repo = self._authenticate_repo()
        openai.api_key = self.openai_api_key

    def _validate_env_variables(self):
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN must be set as an environment variable.")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set as an environment variable.")

    def _authenticate_repo(self):
        try:
            repo = self.github.get_repo(self.repo_name)
            logging.info(f"Authenticated to repository: {repo.full_name}")
            return repo
        except GithubException as e:
            self._handle_github_exception(e)

    def _handle_github_exception(self, e):
        error_messages = {
            401: "Authentication failed: Bad credentials. Please check your GITHUB_TOKEN.",
            403: "Access forbidden: You do not have the necessary permissions.",
            404: "Repository not found: Please check the repository name and your permissions."
        }
        logging.error(error_messages.get(e.status, f"An error occurred: {e.data['message']}"))
        raise

    def create_branch(self):
        default_branch = self.repo.default_branch
        new_branch_name = f'code-improvements-{datetime.datetime.now():%Y%m%d%H%M%S}'
        sb = self.repo.get_branch(default_branch)
        self.repo.create_git_ref(ref=f'refs/heads/{new_branch_name}', sha=sb.commit.sha)
        return new_branch_name, sb

    def improve_code(self, code):
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that improves Python code quality. Only return the code itself."},
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
                self._process_python_file(file_content, default_branch, element_list)

        return element_list

    def _process_python_file(self, file_content, default_branch, element_list):
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

    def commit_changes(self, element_list, new_branch_name, sb):
        if not element_list:
            logging.info('No Python files found to improve.')
            return

        base_tree = self.repo.get_git_tree(sb.commit.sha)
        tree = self.repo.create_git_tree(element_list, base_tree)
        parent = self.repo.get_git_commit(sb.commit.sha)
        commit_message = 'Automated code improvements using GPT-4'
        commit = self.repo.create_git_commit(commit_message, tree, [parent])
        self.repo.get_git_ref(f'heads/{new_branch_name}').edit(commit.sha)

        # Create a Pull Request
        pr = self.repo.create_pull(
            title='Automated Code Improvements',
            body='This PR includes code improvements made by GPT-4.',
            head=new_branch_name,
            base=self.repo.default_branch
        )
        logging.info(f'Pull Request created: {pr.html_url}')

    def run(self):
        new_branch_name, sb = self.create_branch()
        element_list = self.process_files(self.repo.default_branch, new_branch_name, sb)
        self.commit_changes(element_list, new_branch_name, sb)

if __name__ == "__main__":
    # Uncomment the following lines to run the CodeImprover
    # code_improver = CodeImprover('Cowgirl-AI/cgai-landing-page')
    # code_improver.run()
```