import requests
import os
from typing import List

BASE_URL = "https://3.basecampapi.com/{account_id}"


class BasecampDataFetcher:
    def __init__(self, account_id: str, access_token: str):
        self.account_id = account_id
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def fetch_hq(self) -> List[str]:
        url = f"{BASE_URL}/my/hq.json"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        hq_data = response.json()
        return [f"HQ Name: {hq_data['name']}{os.linesep}Description: {hq_data['description']}"]

    def fetch_projects(self) -> List[str]:
        url = f"{BASE_URL}/projects.json"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        projects_data = response.json()
        projects = []
        for project in projects_data:
            project_str = f"Project Name: {project['name']}{os.linesep}Description: {project['description']}"
            todos = self.fetch_todos(project["id"])
            messages = self.fetch_messages(project["id"])
            documents = self.fetch_documents(project["id"])
            project_str += f"{os.linesep}Todos: {os.linesep.join(todos)}"
            project_str += f"{os.linesep}Messages: {os.linesep.join(messages)}"
            project_str += f"{os.linesep}Documents: {os.linesep.join(documents)}"
            projects.append(project_str)
        return projects

    def fetch_todos(self, project_id: str) -> List[str]:
        url = f"{BASE_URL}/buckets/{project_id}/todos.json"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        todos_data = response.json()
        return [
            f"Todo Name: {todo['name']}{os.linesep}Description: {todo['description']}{os.linesep}Due At: {todo['due_at']}"
            for todo in todos_data
        ]

    def fetch_messages(self, project_id: str) -> List[str]:
        url = f"{BASE_URL}/buckets/{project_id}/messages.json"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        messages_data = response.json()
        return [
            f"Message Subject: {message['subject']}{os.linesep}Content: {message['content']}"
            for message in messages_data
        ]

    def fetch_documents(self, project_id: str) -> List[str]:
        url = f"{BASE_URL}/buckets/{project_id}/documents.json"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        documents_data = response.json()
        return [
            f"Document Title: {document['title']}{os.linesep}Content: {document['content']}"
            for document in documents_data
        ]
