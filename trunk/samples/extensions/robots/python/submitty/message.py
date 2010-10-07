# Strings used by robot when accidentally added
ACC_TITLE = 'Hi there!'
ACC_MESSAGE = """I am a robot that helps put extensions in the gallery. I hope you are enjoying the extensions! Please post in the help group if you have any questions about them.\n
http://www.google.com/support/forum/p/wave/label?lid=1fe2aa0c757c9191&hl=en
"""

# Strings used in actual submission wave
TITLE = 'Extension Submission'

INTRO = """
Congratulations on completing your extension!

Welcome to the extension review process. We have put together a series of questions that will help us learn more about your extension and how users will use it inside Wave. When you are done responding, you can let us know by clicking the "Share with Reviewers" button above. If you haven't yet, we suggest reading through the <a href="http://code.google.com/apis/wave/extensions/designprinciples.html">design principles</a> and <a href="http://code.google.com/apis/gadgets/docs/publish.html#Hi_Volume">gadgets performance</a> docs.

First, some basic info about you:
"""

DEV_FIELDS = [
    {'name': 'dev_name', 'label': 'Developer/Company Name'},
    {'name': 'location', 'label': 'Location'}
    ]

MIDDLE = """
Now, some info about your extension:
"""

EXT_FIELDS = [
    {'name': 'samplewave',
     'label': 'Sample Wave',
     'extra': 'Please host on Google Wave Preview. If it is not a public wave, please add google-wave-extensions-review@googlegroups.com to the wave so that we can access it.'},
    {'name': 'installer_url',
     'label': 'Installer URL'}
    ]

ROBOT_QS = """
Great! Please answer the following questions about the robot:

- For each event that the robot reacts to, how does it respond?
- Does the user have to know some special syntax for using your robot? (We recommend avoiding this when possible)
"""

GADGET_QS = """
Great! Please answer the following questions about the gadget:

- What data is shared in the state object? Please describe the key/value mapping.
- How frequenty is the state updated?
- Does the gadget use setModeCallback to provide different behavior in edit versus view mode? If so, please describe.
- What does the user see in playback mode?
- How does one user know what/where another user is editing?
- Is the gadget constant sized? If not, please describe the gadget resizing.
- Does the gadget provide instructions to users?
- What other resources (images/data) does your gadget bring in? For each resource, please note the server that the resource is on, and if you are using gadget caching or some other caching technique.

Please also consider these tips:
- To increase the virality of your extension, we recommend adding a link from the gadget to a public wave with an installer.
- To get feedback on your extension, we suggest adding a link from the gadget to a feedback form, issue tracker, or a public discussion wave.
"""


GAE_QS = """
Okay, please answer these questions about your App Engine use:

- What additional web services does it contact? For each web service, please note the rate limits and expected load of that service.
- Have you enabled billing for your app? If not, please monitor the app to ensure it stays below the free quota limits.
- If you are using a datastore on App Engine, please describe the reads and writes, and whether memcache is being used to cache hits.
- If storing static files on App Engine, please note the cache headers that you've used.
- If rendering dynamic pages on App Engine, please comment on the use of memcache for caching these renders.
"""

EXT_QS = [
    {'name': 'robotqs',
     'label': 'Does your extension include a robot?',
     'response': ROBOT_QS},
    {'name': 'gadgetqs',
     'label': 'Does your extension include a gadget?',
     'response': GADGET_QS},
    {'name': 'gaeqs',
     'label': 'Does your extension use App Engine?',
     'response': GAE_QS}
    ]
