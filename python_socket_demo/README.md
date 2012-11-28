
# App Engine Socket API Example

This is a demo app that shows use of the App Engine Socket API, via the
nntplib module. The nntp server object is created (and the socket connection
opened) in a client request instance, and summary info about the newsgroup
obtained; then the pickled nntp server object is passed in a task queue task
payload to a (potentially) different instance, where it is used further to
fetch the details of the first N posts.  The task queue task pings the client
via the Channel API when it has fetched the posts and stored them in the
datastore, and then the client retrieves the post data from the datastore.
This simple app does no caching or entity reuse, but could easily be extended
to do so.

This app will not run locally using the dev app server; it must be deployed.

Before you can successfully deploy the app, your app id must be whitelisted as
a Socket API Trusted Tester app.
