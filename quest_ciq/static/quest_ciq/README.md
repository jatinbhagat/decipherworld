# Quest CIQ Static Files

This directory is reserved for app-specific static assets such as:

- CSS files (custom styles)
- JavaScript files (custom scripts)
- Images (logos, icons, illustrations)
- Fonts (custom typography)

## Usage

Place your static files in appropriate subdirectories:

```
quest_ciq/static/quest_ciq/
├── css/
│   └── custom.css
├── js/
│   └── quest_ciq.js
├── img/
│   └── logo.png
└── fonts/
    └── custom-font.woff2
```

## Loading Static Files

In templates, load static files using:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'quest_ciq/css/custom.css' %}">
<script src="{% static 'quest_ciq/js/quest_ciq.js' %}"></script>
<img src="{% static 'quest_ciq/img/logo.png' %}" alt="Quest CIQ">
```

## Note

Currently using global Tailwind CSS + DaisyUI from base template.
Add custom assets here as needed.
