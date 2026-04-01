import requests
import urllib.parse
import base64
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class GitLabFile:
    file_name: str
    file_path: str
    size: int
    content: str
    ref: str
    blob_id: str
    commit_id: str
    last_commit_id: str
    encoding: str = "base64"


class GitLabClient:
    def __init__(self, gitlab_url: str, private_token: str):
        self.gitlab_url = gitlab_url.rstrip("/")
        self.private_token = private_token
        self.api_base = f"{self.gitlab_url}/api/v4"
        self.headers = {
            "PRIVATE-TOKEN": private_token,
            "Content-Type": "application/json"
        }

    def _encode_path(self, path: str) -> str:
        return urllib.parse.quote(path, safe="")

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.api_base}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response

    def get_file_raw(
        self,
        project_id: str,
        file_path: str,
        ref: str = "main"
    ) -> str:
        encoded_project = self._encode_path(str(project_id))
        encoded_file = self._encode_path(file_path)

        endpoint = f"/projects/{encoded_project}/repository/files/{encoded_file}/raw?ref={ref}"
        response = self._request("GET", endpoint)

        return response.text

    def get_file(
        self,
        project_id: str,
        file_path: str,
        ref: str = "main"
    ) -> GitLabFile:
        encoded_project = self._encode_path(str(project_id))
        encoded_file = self._encode_path(file_path)

        endpoint = f"/projects/{encoded_project}/repository/files/{encoded_file}?ref={ref}"
        response = self._request("GET", endpoint)

        data = response.json()

        if data.get("encoding") == "base64" and "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8")
        else:
            content = data.get("content", "")

        return GitLabFile(
            file_name=data["file_name"],
            file_path=data["file_path"],
            size=data["size"],
            content=content,
            ref=data["ref"],
            blob_id=data["blob_id"],
            commit_id=data["commit_id"],
            last_commit_id=data["last_commit_id"],
            encoding=data.get("encoding", "base64")
        )

    def get_project_info(self, project_id: str) -> Dict[str, Any]:
        encoded_project = self._encode_path(str(project_id))
        endpoint = f"/projects/{encoded_project}"
        response = self._request("GET", endpoint)
        return response.json()

    def list_repository_tree(
        self,
        project_id: str,
        path: str = "",
        ref: str = "main",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        encoded_project = self._encode_path(str(project_id))
        params = {
            "ref": ref,
            "recursive": str(recursive).lower()
        }
        if path:
            params["path"] = path

        endpoint = f"/projects/{encoded_project}/repository/tree"
        response = self._request("GET", endpoint, params=params)
        return response.json()

    def get_file_blame(
        self,
        project_id: str,
        file_path: str,
        ref: str = "main"
    ) -> List[Dict[str, Any]]:
        encoded_project = self._encode_path(str(project_id))
        encoded_file = self._encode_path(file_path)

        endpoint = f"/projects/{encoded_project}/repository/files/{encoded_file}/blame?ref={ref}"
        response = self._request("GET", endpoint)
        return response.json()

    def get_branches(
        self,
        project_id: str,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        encoded_project = self._encode_path(str(project_id))
        params = {}
        if search:
            params["search"] = search

        endpoint = f"/projects/{encoded_project}/repository/branches"
        response = self._request("GET", endpoint, params=params)
        return response.json()

    def file_exists(
        self,
        project_id: str,
        file_path: str,
        ref: str = "main"
    ) -> bool:
        encoded_project = self._encode_path(str(project_id))
        encoded_file = self._encode_path(file_path)

        endpoint = f"/projects/{encoded_project}/repository/files/{encoded_file}?ref={ref}"
        try:
            self._request("HEAD", endpoint)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return False
            raise

    def list_projects(
        self,
        search: Optional[str] = None,
        per_page: int = 20,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        params = {
            "per_page": per_page,
            "page": page,
            "membership": True
        }
        if search:
            params["search"] = search

        endpoint = "/projects"
        response = self._request("GET", endpoint, params=params)
        projects = response.json()

        filtered_projects = []
        for project in projects:
            filtered_projects.append({
                "id": project.get("id"),
                "name": project.get("name"),
                "name_with_namespace": project.get("name_with_namespace"),
                "http_url_to_repo": project.get("http_url_to_repo"),
                "web_url": project.get("web_url")
            })
        return filtered_projects

    def list_all_projects(
        self,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        all_projects = []
        page = 1
        per_page = 100

        while True:
            projects = self.list_projects(
                search=search,
                per_page=per_page,
                page=page
            )
            if not projects:
                break
            all_projects.extend(projects)
            if len(projects) < per_page:
                break
            page += 1

        return all_projects
