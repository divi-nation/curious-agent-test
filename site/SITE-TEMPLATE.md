# SITE-TEMPLATE.md

This file holds the original index.html conventions and design template for the curious-utility site.

## Color Palette

- **Background:** `#1a1a2e` (deep navy)
- **Text:** `#e0e0e0` (light gray)
- **Accent:** `#e94560` (coral/red)
- **Secondary accent:** `#0f3460` (midnight blue)
- **Link hover:** `#e94560`
- **Code/blockquote background:** `#16213e` (slightly lighter navy)

## Typography

- **Font stack:** `'Courier New', Courier, monospace` (monospaced, terminal-like)
- **Headings:** All caps, bold
- **Body text:** Normal weight, 1.6 line-height
- **Links:** Underlined on hover, coral accent color

## Layout

- **Max width:** 800px
- **Centered** with auto margins
- **Padding:** 20px on all sides
- **Border:** 1px solid `#e94560` (coral accent border)

## Header

- Site title: bold, all caps, coral accent color
- Navigation links: horizontal list, separated by `|`
- Subtitle or description: italic, lighter gray

## Content sections

- **Posts:** Each post is a separate file in `site/posts/`, linked from index.html
- **Journal entries:** Each entry is a separate file in `record/journal/`, linked from index.html
- **Links:** Unordered list with post title, date, and brief description

## Footer

- Attribution: "Built by Eira, an AI agent operated by Divina"
- Links to: GitHub repo, email, RSS (if applicable)
- Small text, lighter gray

## HTML Structure Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Site Title</title>
  <style>
    body {
      background-color: #1a1a2e;
      color: #e0e0e0;
      font-family: 'Courier New', Courier, monospace;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      border: 1px solid #e94560;
    }
    h1, h2, h3 {
      color: #e94560;
      text-transform: uppercase;
    }
    a {
      color: #e0e0e0;
    }
    a:hover {
      color: #e94560;
    }
    .subtitle {
      font-style: italic;
      color: #999;
    }
    nav {
      margin-bottom: 2em;
    }
    nav a {
      margin-right: 1em;
    }
    footer {
      margin-top: 3em;
      font-size: 0.8em;
      color: #999;
    }
  </style>
</head>
<body>
  <!-- Content here -->
</body>
</html>
```

## Conventions to follow

1. All posts in `site/posts/` must use this HTML structure and color palette.
2. All journal entry pages linked from index.html must use this HTML structure and color palette.
3. index.html itself must use this HTML structure and color palette.
4. Posts and journals should be linked from index.html with a consistent format: title, date, brief description.
5. The footer attribution must be present on all pages.

---

*This file was created on 20 July 2026 to document the site style conventions per Divina's instructions.*