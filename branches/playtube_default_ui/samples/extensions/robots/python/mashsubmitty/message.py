intro = """
Congratulations on completing your extension!

Welcome to the extension review process. We have put together a series of questions that will help us learn more about your extension and how users will use it inside Wave. When you are done responding, you can let us know by clicking the "Share with Reviewers" button above. 

<b>First, some basic info about you:</b>
"""

middle = """
<b>Now, some info about your extension:</b>
"""

team_fields = [
    {'name': 'team_name', 'label': 'Developer/Team Name'},
    {'name': 'location', 'label': 'Location'}
    ]

ext_fields = [
    {'name': 'name',
     'label': 'Name'},
    {'name': 'email',
     'label': 'Email'},
    {'name': 'summary',
     'label': 'Summary',
     'extra': '100 chars'},
    {'name': 'description',
     'label': 'Description',
     'type': 'textarea',
     'extra': '100 words'},
    {'name': 'sample_wave',
     'label': 'Sample Wave',
     'extra': 'Please make it a public wave on Google Wave Preview.'},
    {'name': 'screenshot',
     'label': 'Screenshot',
     'extra': 'Please link to a public URL. Desired is 600x300px.'},
    {'name': 'installer_url',
     'label': 'Installer URL'}
]
