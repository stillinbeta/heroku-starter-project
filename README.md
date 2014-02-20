heroku-starter-project
======================

Setup
-----
Setup is really manual atm. Lots of `# TODO`s here.
* You can add repositories using the web interface.
    * On trello, use Sidebar -> Menu -> Share, Print, and Export -> Export JSON to find the board and list IDs
* Users have to be manually inserted into the database. You can get user username from the JSON export above.
    * `INSERT INTO "user" (github_user, trello_user) values ('user', '51d3212606fb87a58d000cee');`
* Create a trello user for your bot.
* Invite the bot to join the board you'd like to use.
* Generate keys for your application here: `https://trello.com/1/appKey/generate`
* Get a token for the bot user:
    * `https://trello.com/1/authorize?key=<your_key>&name=heroku_starter&response_type=token&expiration=never&scope=read,write`
* Use heroku config to save the values for the application:
    * `heroku config SET TRELLO_API_KEY=<API_KEY> TRELLO_API_SECRET=<API_SECRET> TRELLO_TOKEN=<your_token>`
* Set up the Github web hooks to point to your application.
    * You'll need to add the hooks for `pull_request`, `issues`, `pull_request_review_comment`, and `issue_comment`
    * Here's the curl command to use:
```shell
    curl -u "<your username>" -i \
    https://api.github.com/hub \
    -F "hub.mode=subscribe" \
    -F "hub.topic=https://github.com/<repo owner>/<repo name>/events/<hook>" \
    -F "hub.callback=http://<your url>.herokuapp.com/hooks/<the repository id>/<hook>"
```
