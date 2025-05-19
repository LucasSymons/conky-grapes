name: Bug Report
description: File a bug report
about: Use this template for submitting bugs.
title: "[Bug]: " # (Title for your issue. Example: "Conky not displaying after upgrade")
labels: ["bug", "triage"]

body:
    - type: markdown
    attributes:
        value: |
        Thanks for taking the time to fill out this bug report!
        Please provide a little details and background on the issue and fill in the generic questions.
    - type: textarea
    id: what-happened
    attributes:
        label: What happened?
        description: Also tell us, what did you expect to happen?
        placeholder: Tell us what you see!
        value: "A bug happened!"
    validations:
        required: true
    - type: textarea
    id: GNU-Linux
    attributes:
        label: GNU/Linux Version?
        description: Which GNU/Linux Distribution are your using?
        placeholder: Arch
        value: ""
    validations:
        required: true
    - type: textarea
    id: conky-output
    attributes:
        label: Conky Output?
        description: What is the output of the console when calling conky in verbose mode??
        placeholder: ""
        value: ""
    validations:
        required: true
    - type: checkboxes
        id: readme
        attributes:
        label: I have read the readme.md
        description: By submitting this issue, you agree you have read the readme
        options:
            - label: I swear I read the readme
            required: true