from github import Github
from github import Auth
from flask import Flask, request
from flask_cors import CORS
from pytrends.request import TrendReq
import os
import dotenv 

class GithubData:
    def __init__(self, token):
        auth = Auth.Token(token)
        self.g = Github(auth=auth)
        self.g.get_user().login
        self.github_data = []

    def get_data(self, repository):
        print(f'Fetching data for {repository} Repository...')
        try:
            repo = self.g.get_repo(repository)
            # print(dir(repo))

            # PR's
            count = 0
            n_latest = 30
            latest_open_issues = []
            open_issues = repo.get_issues(state='open')
            for issue in open_issues:
                if count == n_latest:
                    count = 0
                    break
                latest_open_issues.append({
                    "issue" : issue.title,
                    "user" : issue.user.login,
                    "href" : f'https://github.com/{repository}/pull/{issue.number}'
                })
                count += 1

            # Releases
            last_releases = []
            releases = repo.get_releases()
            for release in releases:
                if count == n_latest:
                    count = 0
                    break 
                last_releases.append({
                    "release" : release.title
                })
                count += 1

            # Languages
            languages = []
            repo_languages = repo.get_languages()
            for language in repo_languages:
                languages.append({
                    "language" : language,
                    "loc" : repo_languages[language]
                })

            # Contributors
            contributors = 0
            page = 0
            not_empty = True
            while not_empty:
                curr_page = repo.get_contributors(anon=True).get_page(page)
                if len(curr_page) == 0:
                    not_empty = False
                    break
                for item in curr_page:
                    contributors += 1
                page += 1

            # Commits
            commits_data = []
            page = 0
            pages_to_fetch = 25
            while page < pages_to_fetch:
                curr_page = repo.get_commits().get_page(page)
                for item in curr_page:
                    try:
                        commits_data.append({
                            "author" : item.author.login,
                            "date" : str(item.last_modified_datetime.date())
                        })
                    except:
                        continue
                page += 1
            commits_data = commits_data[::-1]

            commits_per_day = {}
            for data in commits_data:
                date = data["date"]
                if date not in commits_per_day:
                    commits_per_day[date] = 1
                else:
                    commits_per_day[date] += 1

            commits_per_day_list = []
            for commit_date in commits_per_day:
                commits_per_day_list.append({
                    "date" : commit_date,
                    "commits" : commits_per_day[commit_date]
                })

            # Contributors
            top_contributors = {}
            for data in commits_data:
                author = data["author"]
                if author not in top_contributors:
                    top_contributors[author] = 1
                else:
                    top_contributors[author] += 1
            top_contributors = dict(sorted(top_contributors.items(), key=lambda item: item[1], reverse=True))

            top_contributors_list = []
            top_n_contributors = 10
            curr_count = 0
            for contributor in top_contributors:
                if curr_count == top_n_contributors:
                    break
                top_contributors_list.append({
                    "author" : contributor,
                    "commits" : top_contributors[contributor]
                })
                curr_count += 1

            # Google trends data(Interest Over Time)
            pytrends = TrendReq(hl='en-US', tz=360)
            kw_list = [repo.name]
            pytrends.build_payload(kw_list, cat=0, timeframe='today 1-m', geo='', gprop='')

            interest_over_time_df = pytrends.interest_over_time().reset_index()
            interest_over_time_df["da_te"] = interest_over_time_df["date"].apply(lambda x : x.strftime("%Y-%m-%d"))
            interest_over_time_df = interest_over_time_df.drop(["date", "isPartial"], axis=1)
            interest_over_time_list = interest_over_time_df.values.tolist()

            topic_interest = []
            for item in interest_over_time_list:
                topic_interest.append({
                    "popularity" : item[0],
                    "date" : item[1]
                })

            temp_data = {
                "repoName" : repo.name,
                "description": repo.description,
                "stars" : repo.stargazers_count,
                "forks" : repo.forks_count,
                "created_at" : repo.created_at,
                "updated_at" : repo.updated_at,
                "homepage" : repo.homepage,
                "latest_open_issues" : latest_open_issues,
                "releases" : last_releases,
                "languages" : languages,
                "contributors" : contributors,
                "latest_release" : last_releases[0]["release"],
                "commits_per_day" : commits_per_day_list,
                "top_contributors" : top_contributors_list,
                "topic_interest" : topic_interest
            }
            return temp_data
        except:
            return f'{repository} not found'


app = Flask(__name__)
CORS(app)

dotenv.load_dotenv()

@app.route('/')
def hello():
    return "hello from flask!"

@app.route('/reponame', methods=['POST'])
def get_repo_data():
    token = os.getenv('TOKEN')
    query = request.args.get('query')
    git_hub = GithubData(token)
    data = git_hub.get_data(query)
    return data

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)


# flask --app app --debug run

# Docker
# docker build -t githubapp .
# docker run -p 5000:5000 githubapp
# docker tag githubapp deysarkarrohan/githubappflask:v1.0 
# docker push deysarkarrohan/githubflaskapp:v1.0




