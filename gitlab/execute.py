from fileinput import filename
import requests
from gitlab_client import GitLabClient
import re
GITLAB_URL = "http://gitlab.com/"
PRIVATE_TOKEN = "PRIVATE_TOKEN"

target_versions = ["1.14.1", "0.34.0"]

def find_versions_in_file(file_content, search_name):
    pattern = rf'"{search_name}"\s*:\s*"([^"]*)"'
    matches = re.findall(pattern, file_content)
    return matches

def check_target_versions(found_versions):
    matched = [v for v in found_versions if v in target_versions]
    return matched

client = GitLabClient(GITLAB_URL, PRIVATE_TOKEN)

def main(filename, search_name):
    try:
        print("=" * 50)
        projects = client.list_all_projects()
        print(f"共有 {len(projects)} 个项目\n")
        for project in projects:
            if("CGM" in project['name_with_namespace']):
                branches = client.get_branches(project['id'])
                for branch in branches:
                    if client.file_exists(project['id'], filename, branch['name']):
                        fileContent = client.get_file(project['id'], filename, branch['name'])
                        if fileContent.content:
                            found_versions = find_versions_in_file(fileContent.content, search_name)
                            versions_str = '无' if len(found_versions) == 0 else ', '.join(found_versions)
                            print(f"名称: {project['name']} - 分支: {branch['name']} - 文件: {filename} - 包: {search_name} - 发现版本: {versions_str}")
                            matched = check_target_versions(found_versions)
                            if matched:
                                print(f"\033[31m名称: {project['name']} - 分支: {branch['name']} - 文件: {filename} - 包: {search_name} - 发现目标版本: {', '.join(matched)}\033[0m")
                            else:
                                print(f"名称: {project['name']} - 分支: {branch['name']} - 文件: {filename} - 包: {search_name} - 目标版本未找到")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP 错误：{e}")
        if e.response is not None:
            print(f"响应内容：{e.response.text}")
    except Exception as e:
        print(f"错误：{e}")

if __name__ == "__main__":
    for filename in ['package-lock.json', 'package.json']:
        main(filename, "axios")


