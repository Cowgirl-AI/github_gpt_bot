from dotenv import load_dotenv
from github import Github, InputGitTreeElement, GithubException
import base64
import datetime
import logging
import os
import openai

load_dotenv()

logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class AutoUpdate: 
    """
    AutoUpdate 
    ----------
    Class to handle automatically updating and refining code in a Github repository, taking advantage of GPT.
    Authenticate processes with the OpenAI API and Github API
    """

    def __init__(self, repository_name: str, repository_owner: str):
        self.repository_name = repository_name
        self.repository_owner = repository_owner

        self.github = Github(os.getenv('GITHUB_TOKEN'))
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.repo = self.github.get_repo(f'{self.repository_owner}/{self.repository_name}')
        self.default_branch = self.repo.default_branch
        self.sb = self.repo.get_branch(self.default_branch)
        self.new_branch_name = self._init_new_branch()
        assert self._is_github_auth_successful(), "GitHub authentication failed."

    def _is_github_auth_successful(self):
        try:
            self.github.get_user().login
            logging.info(f"Authenticated with Github as {self.github.get_user().login}")
            return True
        except GithubException as e:
            logging.error(f"Github authentication failed: {e}")
            return False
        
    
    def _init_new_branch(self):
        # Create a new branch with a timestamp
        new_branch_name = f'code-improvements-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        self.repo.create_git_ref(ref='refs/heads/' + new_branch_name, sha=self.sb.commit.sha)
        logging.info(f"Initialized new branch: {new_branch_name}")
        return new_branch_name

    def send_to_gpt(self, file_content, decoded_content):
        # Send code to GPT for improvement
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that improves Python code quality. Only return the code itself."},
                {"role": "user", "content": f"Improve the following Python code for better readability, efficiency, and compliance with PEP8 standards:\n\n{decoded_content}"}
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        return response.choices[0].message.content.strip()

    
    def repo_file_search(self):
        # List to hold updated files
        element_list = []

        # Iterate over files in the repository
        contents = self.repo.get_contents("", ref=self.default_branch)
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))

            elif file_content.path.endswith('.py'):
                # For large files, fetch content properly
                if file_content.size > 1_000_000:
                    file_content = self.repo.get_contents(file_content.path, ref=self.default_branch)
                
                # Decode file content
                decoded_content = base64.b64decode(file_content.content).decode('utf-8')
                improved_code = self.send_to_gpt(file_content, decoded_content)

                # Prepare the updated file for commit
                element = InputGitTreeElement(
                    path=file_content.path,
                    mode='100644',
                    type='blob',
                    content=improved_code
                )
                element_list.append(element)
                logging.info(f"Improved file: {file_content.path}")
        return element_list
    
    def commit_changes(self, element_list):
        if element_list:
            base_tree = self.repo.get_git_tree(self.sb.commit.sha)
            tree = self.repo.create_git_tree(element_list, base_tree)
            parent = self.repo.get_git_commit(self.sb.commit.sha)
            commit_message = 'Automated code improvements using GPT-4'
            commit = self.repo.create_git_commit(commit_message, tree, [parent])
            self.repo.get_git_ref('heads/' + self.new_branch_name).edit(commit.sha)

            # Create a Pull Request
            pr = self.repo.create_pull(
                title='Automated Code Improvements',
                body='This PR includes code improvements made by GPT-4.',
                head=self.new_branch_name,
                base=self.default_branch
            )
            logging.info(f'Pull Request created: {pr.html_url}')
        else:
            logging.info('No Python files found to improve.')

if __name__ == "__main__":
    auto_update = AutoUpdate(repository_name='teraearlywine', repository_owner='teraearlywine')
    updated_files = auto_update.repo_file_search()
    auto_update.commit_changes(updated_files)

# Improvements made:
# - Added assertions for GitHub authentication.
# - Added logging for branch initialization and file improvements.
# - Wrapped the execution in a main guard to allow for module import without execution.