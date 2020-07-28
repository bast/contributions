import requests
import os


PERSONAL_ACCESS_TOKEN = os.environ.get("PERSONAL_ACCESS_TOKEN", "")


def run_graphql_query(query):
    headers = {"Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}"}
    request = requests.post(
        "https://api.github.com/graphql", json={"query": query}, headers=headers
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(f"Query failed to run by returning code {request.status_code}")


def fetch_repos_batch(category, after, parameters):
    query = """
{
  viewer {
"""
    if after is None:
        query += f"    {category}({parameters}) {{"
    else:
        query += f'    {category}(after: "{after}", {parameters}) {{'
    query += """
      totalCount
      nodes {
        nameWithOwner
        stargazers {
          totalCount
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""
    query_result = run_graphql_query(query)
    _repos = query_result["data"]["viewer"][category]

    repos = _repos["nodes"]
    has_next_page = _repos["pageInfo"]["hasNextPage"]
    end_cursor = _repos["pageInfo"]["endCursor"]

    return repos, has_next_page, end_cursor


def fetch_repos(category, parameters):
    has_next_page = True
    end_cursor = None
    result = []
    while has_next_page:
        repos, has_next_page, end_cursor = fetch_repos_batch(
            category=category, after=end_cursor, parameters=parameters
        )
        for repo in repos:
            name = repo["nameWithOwner"]
            num_stars = repo["stargazers"]["totalCount"]
            result.append((num_stars, name))
    return result


print("contributed to:")
for (num_stars, name) in reversed(
    sorted(
        fetch_repos(
            category="repositoriesContributedTo",
            parameters="first: 100, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]",
        )
    )
):
    print(f"- https://github.com/{name} ({num_stars})")


print("\nas owner:")
for (num_stars, name) in reversed(
    sorted(fetch_repos(category="repositories", parameters="first: 100",))
):
    print(f"- https://github.com/{name} ({num_stars})")
