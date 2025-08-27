# claude_code.md – Prompts for Django + Supabase Website Code Generation

## 1. Project Setup
Prompt:  
Generate step-by-step commands to initialize a Django project called `decipherworld`, add a `core` app, set up for deployment on Render.com, and connect with Supabase for authentication and data (PostgreSQL). Assume a fresh environment.

---

## 2. Django Project Structure
Prompt:  
Generate the recommended Django project folder structure for a site with landing pages, signup/login, course listings, and a contact/demo form, using templates and class-based views. Use mobile-first design conventions.

---

## 3. Models & Supabase Integration
Prompt:  
Generate Django models for Courses, Schools, Teachers, DemoRequests. Show how to integrate with Supabase for authentication and CRUD, using `supabase-py` or recommended approach.

---

## 4. URLs, Views & Template Setup
Prompt:  
Generate example Django URLs, views (CBV where possible), and templates for:  
- Homepage displaying product highlights and CTAs  
- Courses page listing all courses dynamically  
- Teacher/Admin signup/login with Supabase auth  
- Contact/demo request form  
- Success page/messages

---

## 5. HTML & Tailwind CSS
Prompt:  
Generate responsive, minimal HTML + Tailwind CSS templates for each section (hero, mission, courses, product blurbs, signup, contact form, footer), inserting previously generated site copy in the appropriate places.

---

## 6. Demo Request Form Logic
Prompt:  
Generate Django form and view logic for submitting demo/contact requests, saving to Supabase, with error handling and success feedback on UI.

---

## 7. Deployment
Prompt:  
Generate a production-ready `render.yaml` (or Render.com config), suitable for Django, including static file serving, environment vars, and Github autodeploy.

---

## 8. Instructions for Using Generated Content
Prompt:  
Show how to map the content (site copy, emails, etc) you generated earlier into Django templates, context, and, optionally, translation/lookups for maintainability.

