"""
Static, hand-authored content for the "Mastering Django: Beginner to
Enterprise" seed course — curriculum outline, quiz question banks,
assignment briefs, coding exercises, review text, and student name pools.

Kept as plain Python data (no Faker/Lorem Ipsum — neither is an installed
dependency, and the brief asks for coherent, real educational content) so the
seeding modules can stay focused on ORM writes rather than content authoring.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Course-level content
# ---------------------------------------------------------------------------

COURSE_TITLE = "Mastering Django: Beginner to Enterprise"

COURSE_SUMMARY = (
    "Go from a blank terminal to deploying a production-grade, enterprise-ready "
    "Django platform — models, REST APIs, authentication, Celery, Docker, and "
    "a full capstone LMS build."
)

COURSE_DESCRIPTION = """\
Mastering Django: Beginner to Enterprise is a complete, project-driven path \
through the Django ecosystem, built for developers who want to ship real \
backend systems, not just follow tutorials.

You will start from the absolute basics — installing Python, understanding \
virtual environments, and writing your first view — and progressively work \
up to the patterns used by real engineering teams: a normalized data model \
with the Django ORM, a versioned REST API with Django REST Framework, \
JWT-based authentication, background processing with Celery and Redis, a \
tested and containerized deployment pipeline, and enterprise architecture \
concepts like caching, signals, CQRS, and event-driven design.

Every section pairs conceptual lessons with hands-on practice exercises, a \
graded assignment, and a section quiz, so you are never just watching — \
you are building. The course closes with a full capstone project: an \
enterprise-grade Learning Management System with authentication, payments, \
certificates, and a deployed, observable production build, mirroring \
exactly the kind of system this course itself runs on.

By the end, you will not just know Django's API — you will know how to make \
the architectural decisions a senior backend engineer is expected to make.\
"""

LEARNING_OBJECTIVES = [
    "Install and configure a professional Python and Django development environment from scratch",
    "Explain Django's request/response cycle and MTV architecture in your own words",
    "Design normalized relational data models using the Django ORM, including foreign keys and many-to-many relationships",
    "Write, apply, and reason about database migrations safely",
    "Build a secure authentication system, including a custom user model and JWT-based API auth",
    "Customize the Django admin into a usable internal tool for non-technical staff",
    "Design and ship a versioned REST API using Django REST Framework, including serializers, viewsets, and permissions",
    "Offload slow work to background jobs with Celery and Redis, including scheduled periodic tasks",
    "Write a meaningful automated test suite using pytest-django, factories, and coverage tooling",
    "Containerize a Django application with Docker and serve it behind Gunicorn and NGINX",
    "Apply enterprise architecture patterns — caching, signals, CQRS, and event-driven design — to a real codebase",
    "Design, build, and deploy a complete capstone Learning Management System end to end",
]

PREREQUISITES = [
    "Basic familiarity with the command line (navigating directories, running commands)",
    "Comfort reading and writing simple Python scripts (variables, loops, functions)",
    "A computer able to run Python 3.12 and Docker (Windows, macOS, or Linux)",
    "Basic understanding of what a database table is (no SQL expertise required)",
    "Willingness to type every example yourself rather than copy-pasting",
    "No prior Django or web framework experience required",
]

CATEGORY_PARENT_NAME = "Programming"
CATEGORY_CHILD_NAME = "Backend Development"

TAGS = [
    ("Django", "django"),
    ("Python", "python"),
    ("REST API", "rest-api"),
    ("PostgreSQL", "postgres"),
    ("Authentication", "authentication"),
    ("Deployment", "deployment"),
    ("Docker", "docker"),
    ("Redis", "redis"),
    ("Celery", "celery"),
    ("Enterprise", "enterprise"),
]

THUMBNAIL_PATH = "media/thumbnails/courses/mastering-django-beginner-to-enterprise.png"

PRICE_AMOUNT = "149.00"
CURRENCY = "USD"
LANGUAGE = "en"


# ---------------------------------------------------------------------------
# Curriculum: sections + lessons
#
# Lesson "kind" maps directly to content.Lesson.lesson_type. "video"/"article"
# lessons are ordinary curriculum content; "quiz" and "assignment" are the
# structural marker lesson for that section's real Quiz/Assignment row
# (Lesson has no FK to either — the link is by section, per the model's own
# docstring), so every section carries exactly one of each.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LessonSpec:
    title: str
    kind: str  # "video" | "article" | "quiz" | "assignment"
    is_preview: bool = False


@dataclass(frozen=True)
class SectionSpec:
    title: str
    lessons: list[LessonSpec]


SECTIONS: list[SectionSpec] = [
    SectionSpec(
        "Introduction to Django",
        [
            LessonSpec("Welcome to the Course and What You Will Build", "video", is_preview=True),
            LessonSpec("A Brief History of Django and Why It Still Wins in 2026", "video", is_preview=True),
            LessonSpec("Installing Python 3.12 and Setting Up Your PATH", "video"),
            LessonSpec("Installing Django and Verifying Your Setup", "video"),
            LessonSpec("Setting Up VS Code for Django Development", "video"),
            LessonSpec("Understanding Virtual Environments with venv", "video"),
            LessonSpec("Managing Packages with pip and requirements.txt", "video"),
            LessonSpec("Your First Django Project with startproject", "video"),
            LessonSpec("Hello World: Your First View and URL", "video"),
            LessonSpec("Practice Exercises: Explore the Project Structure", "article"),
            LessonSpec("Section Assignment: Bootstrap Your Own Django Project", "assignment"),
            LessonSpec("Section Quiz: Django Foundations", "quiz"),
        ],
    ),
    SectionSpec(
        "Python Refresher for Django Developers",
        [
            LessonSpec("Why a Python Refresher Matters for Django Developers", "video"),
            LessonSpec("Variables, Data Types, and Mutability", "video"),
            LessonSpec("Control Flow: Conditionals and Loops", "video"),
            LessonSpec("Functions, Arguments, and Scope", "video"),
            LessonSpec("*args and **kwargs in Real Django Code", "video"),
            LessonSpec("Classes, Objects, and __init__", "video"),
            LessonSpec("Decorators: Building Your Own @login_required", "video"),
            LessonSpec("Generators and Iterators for Large Querysets", "video"),
            LessonSpec("Type Hints and Static Typing with mypy", "video"),
            LessonSpec("Practice Exercises: Data Structures Drill", "article"),
            LessonSpec("Section Assignment: Refactor a Script Using Classes and Decorators", "assignment"),
            LessonSpec("Section Quiz: Python Fundamentals", "quiz"),
        ],
    ),
    SectionSpec(
        "Django Fundamentals",
        [
            LessonSpec("The Request/Response Cycle Explained", "video", is_preview=True),
            LessonSpec("Creating Apps with startapp", "video"),
            LessonSpec("Django's URL Dispatcher and Path Converters", "video"),
            LessonSpec("Function-Based Views vs Class-Based Views", "video"),
            LessonSpec("Rendering Templates with the Django Template Language", "video"),
            LessonSpec("Template Inheritance and the block Tag", "video"),
            LessonSpec("Serving Static Files in Development", "video"),
            LessonSpec("Django Settings: Environments and Best Practices", "video"),
            LessonSpec("Working with Forms and Form Validation", "video"),
            LessonSpec("Handling GET and POST Requests Safely", "video"),
            LessonSpec("Practice Exercises: Build a Mini Blog", "article"),
            LessonSpec("Section Assignment: Ship a Static Pages App", "assignment"),
            LessonSpec("Section Quiz: Django Fundamentals", "quiz"),
        ],
    ),
    SectionSpec(
        "Models and the Django ORM",
        [
            LessonSpec("Introduction to the Django ORM", "video"),
            LessonSpec("Defining Your First Model", "video"),
            LessonSpec("Field Types and Field Options", "video"),
            LessonSpec("Making and Applying Migrations", "video"),
            LessonSpec("The Django Admin Meets Your Models", "video"),
            LessonSpec("QuerySets: Filtering, Excluding, and Chaining", "video"),
            LessonSpec("One-to-Many Relationships with ForeignKey", "video"),
            LessonSpec("Many-to-Many Relationships Explained", "video"),
            LessonSpec("One-to-One Relationships and Profile Patterns", "video"),
            LessonSpec("Custom Model Managers", "video"),
            LessonSpec("Model Methods, Properties, and Meta Options", "video"),
            LessonSpec("Practice Exercises: Model a Blog with Comments", "article"),
            LessonSpec("Section Assignment: Design a Normalized Schema", "assignment"),
            LessonSpec("Section Quiz: Models and the ORM", "quiz"),
        ],
    ),
    SectionSpec(
        "Authentication and Authorization",
        [
            LessonSpec("Django's Built-in Authentication System", "video"),
            LessonSpec("Building a Custom User Model the Right Way", "video"),
            LessonSpec("Login and Logout Views", "video"),
            LessonSpec("User Registration and Password Validation", "video"),
            LessonSpec("Permissions: Object-Level vs Model-Level", "video"),
            LessonSpec("Groups and Bulk Permission Management", "video"),
            LessonSpec("Introduction to Token-Based Authentication", "video"),
            LessonSpec("Implementing JWT Authentication with SimpleJWT", "video"),
            LessonSpec("OAuth2 and Social Login Fundamentals", "video"),
            LessonSpec("Multi-Factor Authentication Concepts", "video"),
            LessonSpec("Practice Exercises: Build a Login Flow", "article"),
            LessonSpec("Section Assignment: Add JWT Auth to Your API", "assignment"),
            LessonSpec("Section Quiz: Authentication and Authorization", "quiz"),
        ],
    ),
    SectionSpec(
        "Mastering the Django Admin",
        [
            LessonSpec("Registering Models with the Admin Site", "video"),
            LessonSpec("Customizing List Displays and Search Fields", "video"),
            LessonSpec("Admin Actions: Bulk Operations Made Easy", "video"),
            LessonSpec("Custom Filters and List Filters", "video"),
            LessonSpec("Inline Admin for Related Models", "video"),
            LessonSpec("Admin Permissions and Staff Access", "video"),
            LessonSpec("Overriding Admin Templates", "video"),
            LessonSpec("Practice Exercises: Admin for an E-Commerce App", "article"),
            LessonSpec("Section Assignment: Build a Custom Admin Dashboard", "assignment"),
            LessonSpec("Section Quiz: Django Admin", "quiz"),
        ],
    ),
    SectionSpec(
        "Django REST Framework",
        [
            LessonSpec("Why DRF? APIs in the Modern Web", "video", is_preview=True),
            LessonSpec("Your First APIView", "video"),
            LessonSpec("Serializers: Translating Models to JSON", "video"),
            LessonSpec("ModelSerializer and Nested Serializers", "video"),
            LessonSpec("ViewSets and the DefaultRouter", "video"),
            LessonSpec("Generic Views and Mixins", "video"),
            LessonSpec("Permissions and Authentication in DRF", "video"),
            LessonSpec("Pagination Strategies for Large Datasets", "video"),
            LessonSpec("Filtering, Searching, and Ordering with django-filter", "video"),
            LessonSpec("Throttling and Rate Limiting", "video"),
            LessonSpec("Documenting APIs with drf-spectacular and Swagger", "video"),
            LessonSpec("Practice Exercises: Build a Course Catalog API", "article"),
            LessonSpec("Section Assignment: Ship a Versioned Public API", "assignment"),
            LessonSpec("Section Quiz: Django REST Framework", "quiz"),
        ],
    ),
    SectionSpec(
        "Background Jobs with Celery and Redis",
        [
            LessonSpec("Why Background Jobs Matter", "video"),
            LessonSpec("Installing and Configuring Redis", "video"),
            LessonSpec("Setting Up Celery with Django", "video"),
            LessonSpec("Writing Your First Celery Task", "video"),
            LessonSpec("Sending Emails Asynchronously", "video"),
            LessonSpec("Retries, Timeouts, and Error Handling", "video"),
            LessonSpec("Scheduling Periodic Tasks with Celery Beat", "video"),
            LessonSpec("Monitoring Tasks with Flower", "video"),
            LessonSpec("Practice Exercises: Build a Notification Pipeline", "article"),
            LessonSpec("Section Assignment: Add a Scheduled Digest Email Job", "assignment"),
            LessonSpec("Section Quiz: Celery and Redis", "quiz"),
        ],
    ),
    SectionSpec(
        "Testing Django Applications",
        [
            LessonSpec("Why Testing Matters in Production Systems", "video"),
            LessonSpec("Writing Your First Unit Test", "video"),
            LessonSpec("Testing Views and Responses", "video"),
            LessonSpec("Testing Models and the ORM", "video"),
            LessonSpec("Using Factories with factory_boy", "video"),
            LessonSpec("Mocking External Services", "video"),
            LessonSpec("Integration Tests for API Endpoints", "video"),
            LessonSpec("Measuring Coverage with coverage.py", "video"),
            LessonSpec("Practice Exercises: Test a Payment Flow", "article"),
            LessonSpec("Section Assignment: Reach 90% Coverage on Your Capstone", "assignment"),
            LessonSpec("Section Quiz: Testing Strategies", "quiz"),
        ],
    ),
    SectionSpec(
        "Deployment and DevOps",
        [
            LessonSpec("From localhost to Production: An Overview", "video"),
            LessonSpec("Containerizing Django with Docker", "video"),
            LessonSpec("Writing an Efficient Dockerfile", "video"),
            LessonSpec("Multi-Container Setups with docker-compose", "video"),
            LessonSpec("Serving Django with Gunicorn", "video"),
            LessonSpec("NGINX as a Reverse Proxy", "video"),
            LessonSpec("Configuring PostgreSQL for Production", "video"),
            LessonSpec("Environment Variables and Secrets Management", "video"),
            LessonSpec("Setting Up SSL/TLS Certificates", "video"),
            LessonSpec("Continuous Integration and Deployment Pipelines", "video"),
            LessonSpec("Practice Exercises: Deploy Your Capstone App", "article"),
            LessonSpec("Section Assignment: Ship a Zero-Downtime Deploy Pipeline", "assignment"),
            LessonSpec("Section Quiz: Deployment and DevOps", "quiz"),
        ],
    ),
    SectionSpec(
        "Enterprise Architecture Patterns",
        [
            LessonSpec("Designing for Scale: Enterprise Principles", "video"),
            LessonSpec("Caching Strategies with Redis", "video"),
            LessonSpec("Django Signals: Use and Misuse", "video"),
            LessonSpec("Introduction to CQRS", "video"),
            LessonSpec("Event-Driven Architecture in Django", "video"),
            LessonSpec("Breaking a Monolith into Services", "video"),
            LessonSpec("API Gateways and Service Boundaries", "video"),
            LessonSpec("Observability: Logging, Metrics, and Tracing", "video"),
            LessonSpec("Monitoring with Sentry and Prometheus", "video"),
            LessonSpec("Security Hardening for Enterprise Applications", "video"),
            LessonSpec("Practice Exercises: Refactor Toward Services", "article"),
            LessonSpec("Section Assignment: Add Caching and Signals to Your Capstone", "assignment"),
            LessonSpec("Section Quiz: Enterprise Architecture", "quiz"),
        ],
    ),
    SectionSpec(
        "Capstone Project: Enterprise LMS",
        [
            LessonSpec("Capstone Overview and Requirements", "video", is_preview=True),
            LessonSpec("Architecting the LMS Data Model", "video"),
            LessonSpec("Building Authentication and Roles", "video"),
            LessonSpec("Building the Course Catalog API", "video"),
            LessonSpec("Implementing Payments and Checkout", "video"),
            LessonSpec("Generating Verifiable Certificates", "video"),
            LessonSpec("Adding Background Jobs for Notifications", "video"),
            LessonSpec("Writing Tests for the Capstone", "video"),
            LessonSpec("Containerizing the Capstone Application", "video"),
            LessonSpec("Deploying the Capstone to Production", "video"),
            LessonSpec("Performance Tuning and Caching", "video"),
            LessonSpec("Practice Exercises: Extend the Capstone with a New Feature", "article"),
            LessonSpec("Section Assignment: Submit Your Enterprise LMS Capstone", "assignment"),
            LessonSpec("Section Quiz: Capstone Mastery", "quiz"),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Quizzes — one per section, indexed the same as SECTIONS.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuestionSpec:
    prompt: str
    choices: list[str]
    correct_index: int
    explanation: str


@dataclass(frozen=True)
class QuizSpec:
    title: str
    pass_score: int
    attempts_allowed: int
    questions: list[QuestionSpec]


QUIZZES: list[QuizSpec] = [
    QuizSpec(
        "Section Quiz: Django Foundations",
        70,
        3,
        [
            QuestionSpec(
                "Which command creates a brand-new Django project?",
                ["django-admin startproject", "django-admin startapp", "python manage.py runserver", "pip install django-project"],
                0,
                "startproject scaffolds a new project; startapp scaffolds an app inside an existing project.",
            ),
            QuestionSpec(
                "What is the purpose of a Python virtual environment?",
                ["To isolate project dependencies from the system Python installation", "To compile Python into machine code", "To replace pip entirely", "To run Django in production automatically"],
                0,
                "A venv gives each project its own package set, avoiding version conflicts between projects.",
            ),
            QuestionSpec(
                "Which file is the entry point for running Django management commands?",
                ["manage.py", "settings.py", "wsgi.py", "urls.py"],
                0,
                "manage.py wraps django-admin with your project's settings already configured.",
            ),
            QuestionSpec(
                "What does 'pip freeze > requirements.txt' do?",
                ["Writes installed package versions to a file", "Deletes installed packages", "Upgrades all packages", "Creates a virtual environment"],
                0,
                "requirements.txt lets teammates or servers reproduce your exact dependency versions.",
            ),
            QuestionSpec(
                "Which command starts Django's local development server?",
                ["python manage.py runserver", "python manage.py startserver", "django-admin runserver", "python server.py"],
                0,
                "runserver is a lightweight server for development only — never for production traffic.",
            ),
            QuestionSpec(
                "Why is Django often chosen for enterprise backends?",
                ["It's a batteries-included framework with an ORM, admin, and security defaults built in", "It only supports NoSQL databases", "It requires no third-party packages ever", "It cannot be deployed with Docker"],
                0,
                "Django ships with an ORM, auth, admin, and secure defaults out of the box, cutting a lot of boilerplate.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Python Fundamentals",
        70,
        3,
        [
            QuestionSpec(
                "What does type([]) return?",
                ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"],
                0,
                "Square brackets [] construct a list literal.",
            ),
            QuestionSpec(
                "Which keyword turns a function into a generator?",
                ["yield", "return", "async", "lambda"],
                0,
                "yield pauses and resumes execution, producing a lazy sequence of values instead of one return value.",
            ),
            QuestionSpec(
                "What does **kwargs collect inside a function signature?",
                ["Keyword arguments into a dict", "Positional arguments into a tuple", "Nothing — it's invalid syntax", "A list of default values"],
                0,
                "**kwargs gathers any extra keyword arguments into a dictionary; *args does the equivalent for positional arguments.",
            ),
            QuestionSpec(
                "Which best describes a decorator?",
                ["A function that takes a function and returns a wrapped function", "A class that inherits from object", "A built-in Python keyword", "A type of list comprehension"],
                0,
                "Decorators wrap a callable to add behavior — Django's @login_required is a real-world example.",
            ),
            QuestionSpec(
                "What does print(0.1 + 0.2 == 0.3) output?",
                ["False", "True", "Error", "None"],
                0,
                "Binary floating-point representation means 0.1 + 0.2 is very slightly off from 0.3.",
            ),
            QuestionSpec(
                "Which typing construct declares a function returns either a string or None?",
                ["Optional[str]", "str | error", "None(str)", "Union.str"],
                0,
                "Optional[str] is shorthand for Union[str, None], commonly used for typed Django service functions.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Django Fundamentals",
        70,
        3,
        [
            QuestionSpec(
                "Which file maps URLs to views in a Django app?",
                ["urls.py", "views.py", "models.py", "apps.py"],
                0,
                "urls.py defines URL patterns and points each one at a view function or class.",
            ),
            QuestionSpec(
                "What does {% extends \"base.html\" %} do in a template?",
                ["Inherits blocks from a parent template", "Imports a Python module", "Redirects to another view", "Loads static files"],
                0,
                "Template inheritance lets child templates override specific {% block %} sections of a shared layout.",
            ),
            QuestionSpec(
                "Which decorator restricts a view to POST requests only?",
                ["@require_POST", "@post_only", "@restrict(methods=['POST'])", "@csrf_exempt"],
                0,
                "django.views.decorators.http.require_POST returns a 405 for any other HTTP method.",
            ),
            QuestionSpec(
                "Where is STATIC_URL configured?",
                ["settings.py", "urls.py", "wsgi.py", "manage.py"],
                0,
                "STATIC_URL and related static-file settings live in the project's settings module.",
            ),
            QuestionSpec(
                "What is the core difference between a function-based view and a class-based view?",
                ["CBVs organize HTTP-method handling into methods on a class; FBVs use a single function", "FBVs cannot render templates", "CBVs cannot access request.POST", "There is no meaningful difference"],
                0,
                "A CBV like ListView defines get()/post() as separate methods, which composes well via mixins.",
            ),
            QuestionSpec(
                "Which Django form method checks submitted data against field validators?",
                ["is_valid()", "clean_data()", "validate()", "check()"],
                0,
                "is_valid() runs all field and form-level validation and populates form.cleaned_data on success.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Models and the ORM",
        70,
        3,
        [
            QuestionSpec(
                "Which command generates migration files after model changes?",
                ["python manage.py makemigrations", "python manage.py migrate", "python manage.py syncdb", "python manage.py collectstatic"],
                0,
                "makemigrations detects model changes and writes migration files; migrate then applies them.",
            ),
            QuestionSpec(
                "Which field type represents a many-to-many relationship?",
                ["ManyToManyField", "ForeignKey", "OneToOneField", "related_field"],
                0,
                "ManyToManyField is backed by an automatic (or explicit, via 'through') join table.",
            ),
            QuestionSpec(
                "What does on_delete=models.CASCADE do?",
                ["Deletes related rows when the referenced row is deleted", "Prevents deletion of the referenced row", "Sets the field to NULL on delete", "Archives the row instead of deleting"],
                0,
                "CASCADE propagates deletion; PROTECT and SET_NULL are the common safer alternatives.",
            ),
            QuestionSpec(
                "Which QuerySet method returns a single object or raises DoesNotExist?",
                ["get()", "filter()", "first()", "all()"],
                0,
                "get() expects exactly one match — zero or multiple matches both raise an exception.",
            ),
            QuestionSpec(
                "What is a custom Manager typically used for?",
                ["Encapsulating reusable query logic on a model", "Managing user permissions", "Defining URL routes", "Rendering templates"],
                0,
                "A custom Manager (e.g. Course.objects.published()) keeps common query filters out of view code.",
            ),
            QuestionSpec(
                "Which on_delete option prevents deleting a row if related rows still reference it?",
                ["PROTECT", "CASCADE", "SET_NULL", "DO_NOTHING"],
                0,
                "PROTECT raises ProtectedError instead of allowing the delete, guarding referential integrity.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Authentication and Authorization",
        70,
        3,
        [
            QuestionSpec(
                "Which setting points Django at a custom user model?",
                ["AUTH_USER_MODEL", "USER_MODEL", "CUSTOM_USER", "AUTHENTICATION_MODEL"],
                0,
                "AUTH_USER_MODEL must be set before the first migration — swapping it later is painful.",
            ),
            QuestionSpec(
                "What does the @login_required decorator do?",
                ["Redirects unauthenticated users to the login page", "Deletes the user's session", "Grants superuser access", "Disables CSRF protection"],
                0,
                "It checks request.user.is_authenticated and redirects to LOGIN_URL if not.",
            ),
            QuestionSpec(
                "Which package is the standard choice for JWT auth in DRF?",
                ["djangorestframework-simplejwt", "django-jwt-auth-official", "drf-token-jwt", "pyjwt-django"],
                0,
                "SimpleJWT provides access/refresh token views and a DRF authentication class.",
            ),
            QuestionSpec(
                "What are Django Groups used for?",
                ["Bulk-assigning the same set of permissions to many users", "Grouping templates together", "Grouping URL patterns", "Grouping database migrations"],
                0,
                "Assign permissions to a Group once, then add/remove users from it instead of managing permissions per user.",
            ),
            QuestionSpec(
                "In OAuth2's authorization code grant, what is a code exchanged for?",
                ["An access token", "A username and password", "A CSRF token", "A session cookie only"],
                0,
                "The client sends the authorization code to the token endpoint and receives an access (and often refresh) token.",
            ),
            QuestionSpec(
                "Which HTTP status typically signals missing or invalid credentials?",
                ["401 Unauthorized", "404 Not Found", "500 Internal Server Error", "302 Found"],
                0,
                "401 means authentication is required or has failed; 403 is the related 'authenticated but not permitted' case.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Django Admin",
        70,
        3,
        [
            QuestionSpec(
                "Which call registers a model with the Django admin?",
                ["admin.site.register()", "admin.register_model()", "models.Meta.admin = True", "admin.add()"],
                0,
                "admin.site.register(Model, ModelAdmin) — or the @admin.register decorator — wires a model into /admin/.",
            ),
            QuestionSpec(
                "Which ModelAdmin attribute controls the columns shown in the list view?",
                ["list_display", "list_fields", "display_fields", "admin_fields"],
                0,
                "list_display accepts field names or callables to render as columns.",
            ),
            QuestionSpec(
                "What are admin actions used for?",
                ["Running bulk operations on selected objects in the list view", "Styling the admin theme", "Creating new URL routes", "Sending emails automatically"],
                0,
                "An action is a function that receives the selected queryset, e.g. 'mark selected orders as refunded'.",
            ),
            QuestionSpec(
                "Which classes let you edit related objects inline on a parent's admin page?",
                ["TabularInline / StackedInline", "InlineModelAdmin used directly", "AdminSite", "ModelForm"],
                0,
                "Both subclass InlineModelAdmin and are added via a ModelAdmin's `inlines` attribute.",
            ),
            QuestionSpec(
                "Which attribute adds a sidebar filter to the admin list view?",
                ["list_filter", "filter_fields", "sidebar_filter", "search_fields"],
                0,
                "list_filter renders a right-hand sidebar of filters based on the given fields.",
            ),
            QuestionSpec(
                "Which User flag actually gates login access to the /admin/ site?",
                ["is_staff", "is_admin", "is_superuser_only", "has_admin_access"],
                0,
                "is_staff is required to log into the admin; is_superuser grants all permissions once inside.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Django REST Framework",
        70,
        3,
        [
            QuestionSpec(
                "Which DRF construct combines an entire CRUD resource with router-friendly conventions?",
                ["ViewSet", "APIView", "GenericAPIView", "Serializer"],
                0,
                "A ViewSet groups list/create/retrieve/update/destroy and is registered with a Router in one line.",
            ),
            QuestionSpec(
                "What does a Serializer do in DRF?",
                ["Converts complex data like querysets into JSON and validates incoming data", "Handles URL routing", "Manages database migrations", "Renders HTML templates"],
                0,
                "Serializers are DRF's equivalent of Django Forms — validation plus (de)serialization.",
            ),
            QuestionSpec(
                "Which class auto-generates URL patterns for a registered ViewSet?",
                ["DefaultRouter", "URLPatterns", "ViewSetRouter", "AutoRouter"],
                0,
                "router.register('courses', CourseViewSet) then router.urls gives you the full REST URL set.",
            ),
            QuestionSpec(
                "Which setting controls how many results a paginated DRF endpoint returns per page?",
                ["PAGE_SIZE (via the pagination class config)", "MAX_RESULTS", "RESULTS_PER_PAGE", "LIMIT"],
                0,
                "PAGE_SIZE is read by the configured pagination class, e.g. PageNumberPagination.",
            ),
            QuestionSpec(
                "What does throttling in DRF protect against?",
                ["Excessive request rates from a single client", "SQL injection", "Cross-site scripting", "Broken authentication"],
                0,
                "Throttle classes cap requests per user/IP/scope over a time window.",
            ),
            QuestionSpec(
                "Which tool is the standard choice for auto-generating an OpenAPI schema for a DRF project?",
                ["drf-spectacular", "drf-swagger-official", "openapi-drf", "drf-docs-auto"],
                0,
                "drf-spectacular introspects serializers and views to produce an OpenAPI 3 schema and Swagger UI.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Celery and Redis",
        70,
        3,
        [
            QuestionSpec(
                "What role does Redis typically play in a Celery setup?",
                ["Message broker (and often result backend)", "Web server", "Template engine", "ORM replacement"],
                0,
                "Celery workers pull tasks from the broker queue; Redis is a common, fast choice for that queue.",
            ),
            QuestionSpec(
                "Which decorator turns a plain function into a Celery task?",
                ["@shared_task or @app.task", "@celery_task", "@async_job", "@background"],
                0,
                "@shared_task is the app-agnostic version, useful for reusable tasks across Django apps.",
            ),
            QuestionSpec(
                "What does Celery Beat provide?",
                ["Scheduled, periodic task execution", "Faster task serialization", "A built-in web dashboard", "Database migrations for tasks"],
                0,
                "Beat is a scheduler process that enqueues tasks on a cron-like schedule.",
            ),
            QuestionSpec(
                "Why send emails from a background task instead of inline in a request?",
                ["So slow I/O doesn't block the HTTP response", "Because Django cannot send emails synchronously", "Because SMTP requires Celery", "Because emails must be encrypted by Celery"],
                0,
                "Offloading slow I/O keeps request/response latency low and lets the task retry independently on failure.",
            ),
            QuestionSpec(
                "Which tool provides a real-time web UI for monitoring Celery workers and tasks?",
                ["Flower", "Beat", "Kombu", "Billiard"],
                0,
                "Flower shows active/queued/failed tasks and worker status in a browser dashboard.",
            ),
            QuestionSpec(
                "What's a sensible default strategy when a task fails due to a transient error (e.g. a network blip)?",
                ["Retry with backoff", "Mark it permanently failed immediately", "Silently ignore the failure", "Restart the entire server"],
                0,
                "Celery's retry(countdown=..., max_retries=...) handles exactly this class of transient failure.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Testing Strategies",
        70,
        3,
        [
            QuestionSpec(
                "Which base class gives you a test client and per-test database transaction rollback?",
                ["django.test.TestCase", "unittest.TestCase", "pytest.Case", "django.TransactionOnly"],
                0,
                "TestCase wraps each test in a transaction that's rolled back afterward, keeping tests isolated and fast.",
            ),
            QuestionSpec(
                "What is factory_boy typically used for?",
                ["Generating realistic model instances for tests without repetitive boilerplate", "Replacing the Django ORM", "Running tests in parallel", "Measuring code coverage"],
                0,
                "A Factory class defines sensible defaults for a model so tests can override only what they care about.",
            ),
            QuestionSpec(
                "What does mocking an external service in a test achieve?",
                ["Isolates the test from real network calls and unpredictable third-party behavior", "Makes the test slower but more accurate", "Bypasses all assertions", "Deletes the test database"],
                0,
                "Mocking swaps a real dependency (like a payment gateway) for a controllable stand-in.",
            ),
            QuestionSpec(
                "Which tool reports what percentage of your code the test suite actually executed?",
                ["coverage.py", "pytest-report", "django-coverage-badge", "unittest.coverage"],
                0,
                "coverage.py instruments test runs and reports line/branch coverage per file.",
            ),
            QuestionSpec(
                "What's the key difference between a unit test and an integration test?",
                ["A unit test isolates a single component; an integration test exercises multiple components together", "Unit tests always require a database", "Integration tests never use the test client", "There is no meaningful difference"],
                0,
                "Integration tests catch issues at the seams — e.g. a view, serializer, and model working together correctly.",
            ),
            QuestionSpec(
                "Why run the test suite in CI on every pull request?",
                ["To catch regressions before they reach production", "To slow down development on purpose", "Because CI replaces code review", "To automatically deploy code"],
                0,
                "A CI gate turns 'it works on my machine' into a repeatable, enforced check before merge.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Deployment and DevOps",
        70,
        3,
        [
            QuestionSpec(
                "What does a Dockerfile define?",
                ["The steps to build a container image", "A Kubernetes cluster", "A database schema", "A Celery task queue"],
                0,
                "Each instruction (FROM, COPY, RUN, ...) adds a layer to the resulting image.",
            ),
            QuestionSpec(
                "What is Gunicorn commonly used for in a Django deployment?",
                ["A WSGI application server that runs Django in production", "A reverse proxy", "A database", "A CSS framework"],
                0,
                "Gunicorn runs multiple worker processes to actually execute Django's WSGI application under load.",
            ),
            QuestionSpec(
                "Why put NGINX in front of Gunicorn?",
                ["To handle static files, SSL termination, and reverse-proxy traffic efficiently", "To replace the Django ORM", "To run Celery tasks", "To compile Python bytecode"],
                0,
                "NGINX is far better at serving static assets and terminating TLS than a Python app server.",
            ),
            QuestionSpec(
                "Where should production secrets like SECRET_KEY and database passwords live?",
                ["Environment variables or a secrets manager, never committed to source control", "Hardcoded in settings.py", "In the git commit history", "In the frontend JavaScript bundle"],
                0,
                "Secrets in source control are a permanent leak the moment the repo is ever exposed, even briefly.",
            ),
            QuestionSpec(
                "What does docker-compose let you do?",
                ["Define and run multi-container applications from a single YAML file", "Replace Docker entirely", "Only build images, never run them", "Manage Django migrations"],
                0,
                "A single docker-compose.yml can define web, db, redis, and worker services together.",
            ),
            QuestionSpec(
                "What is the purpose of a CI/CD pipeline?",
                ["Automatically test, build, and deploy code on every change", "Manually FTP files to a server", "Replace version control", "Write documentation automatically"],
                0,
                "CI/CD turns build-test-deploy into a repeatable, automated pipeline instead of manual steps.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Enterprise Architecture",
        70,
        3,
        [
            QuestionSpec(
                "What problem does caching primarily solve?",
                ["Reducing repeated expensive computation or database load by reusing previous results", "Increasing database writes", "Replacing the need for indexes", "Encrypting data at rest"],
                0,
                "A cache trades a small amount of staleness risk for a large reduction in repeated work.",
            ),
            QuestionSpec(
                "What is a Django signal used for?",
                ["Letting decoupled parts of an app react to an event, like post_save", "Defining URL routes", "Rendering templates", "Running migrations"],
                0,
                "Signals let, e.g., a Profile row auto-create whenever a User is saved, without coupling the two apps directly.",
            ),
            QuestionSpec(
                "What does CQRS stand for?",
                ["Command Query Responsibility Segregation", "Central Query Response System", "Cached Query Result Store", "Cross-Quadrant Routing Service"],
                0,
                "CQRS separates the models used to write data (commands) from the ones used to read it (queries).",
            ),
            QuestionSpec(
                "What characterizes event-driven architecture?",
                ["Services communicate by publishing and reacting to events rather than direct synchronous calls", "All services must share one database", "Every request must be synchronous", "Events are only used for logging"],
                0,
                "Producers publish events; any number of independent consumers can react without the producer knowing about them.",
            ),
            QuestionSpec(
                "What's a common risk of overusing Django signals?",
                ["Hidden, hard-to-trace side effects that make control flow difficult to follow", "They are slower than Celery tasks in all cases", "They cannot be tested", "They only work with class-based views"],
                0,
                "A save() that silently triggers five unrelated signal handlers is a classic 'spooky action at a distance' bug source.",
            ),
            QuestionSpec(
                "Why do enterprise systems invest in observability (logging, metrics, tracing)?",
                ["To detect, diagnose, and resolve production issues quickly", "To make the codebase slower on purpose", "To replace the need for testing", "To avoid needing monitoring dashboards"],
                0,
                "Observability shortens the path from 'something is wrong' to 'here is exactly why'.",
            ),
        ],
    ),
    QuizSpec(
        "Section Quiz: Capstone Mastery",
        75,
        3,
        [
            QuestionSpec(
                "In the capstone LMS, what actually determines whether a user can act as an instructor?",
                ["An assigned instructor Role/UserRole record, not just being logged in", "Their email domain", "The color of their profile avatar", "Nothing — every user is automatically an instructor"],
                0,
                "Authorization is role-based: a UserRole row linking the user to the 'instructor' Role is what grants instructor-level access.",
            ),
            QuestionSpec(
                "Why issue a certificate with a unique verification identifier?",
                ["So a third party, like an employer, can verify authenticity via a public link", "To make the PDF file smaller", "To satisfy Celery Beat scheduling", "Because Django requires it for every model"],
                0,
                "A verifiable certificate is only useful if someone besides the student can confirm it's real.",
            ),
            QuestionSpec(
                "What is the benefit of containerizing the capstone application?",
                ["Consistent, reproducible environments across development, staging, and production", "It makes the code run without Python installed", "It automatically writes tests", "It replaces the need for a database"],
                0,
                "\"Works on my machine\" stops being a valid excuse once the whole environment ships in the image.",
            ),
            QuestionSpec(
                "Why design caching into the capstone early rather than bolting it on later?",
                ["Retrofitting caching after code is tightly coupled to raw queries is more error-prone than designing for it upfront", "Caching is only useful for static files", "Django cannot support caching once models exist", "Caching requires rewriting the ORM"],
                0,
                "Cache invalidation is easiest to reason about when it's part of the original data-access design, not patched in later.",
            ),
            QuestionSpec(
                "What is the value of a final code review pass before shipping the capstone?",
                ["Catching maintainability, security, and consistency issues before they reach production", "It replaces automated testing", "It is required by the Python interpreter", "It only checks code formatting"],
                0,
                "Review catches the class of issues tests don't — naming, structure, and judgment calls a linter can't make.",
            ),
            QuestionSpec(
                "What best describes a 'zero-downtime deployment'?",
                ["Rolling out new code without interrupting service for existing users", "Deploying only at midnight", "Deploying without writing any tests", "Deleting the database before each deploy"],
                0,
                "Techniques like rolling/blue-green deploys keep at least one healthy instance serving traffic throughout the rollout.",
            ),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Assignments — one per section, indexed the same as SECTIONS.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssignmentSpec:
    title: str
    instructions: str
    due_in_days: int
    allow_late: bool


ASSIGNMENTS: list[AssignmentSpec] = [
    AssignmentSpec(
        "Bootstrap Your Own Django Project",
        "Create a brand-new Django project named 'portfolio_site' using django-admin startproject. "
        "Inside it, create one app called 'home' with a single view that renders 'Hello, <your name>!' "
        "at the root URL. Submit the GitHub repository link containing your project, with a README "
        "explaining how to set up the virtual environment and run the dev server.",
        7,
        True,
    ),
    AssignmentSpec(
        "Refactor a Script Using Classes and Decorators",
        "You'll be given a 60-line procedural script that processes a list of student grades. "
        "Refactor it into a GradeBook class with methods for adding scores, computing an average, "
        "and printing a report. Add a @timed decorator that logs how long report generation takes. "
        "Submit your refactored script plus a short paragraph explaining your design choices.",
        7,
        True,
    ),
    AssignmentSpec(
        "Ship a Static Pages App",
        "Build a 'pages' app with three routes — /, /about/, and /contact/ — each rendering its own "
        "template that extends a shared base.html with a nav bar. The contact page must include a "
        "form (no submission handling required yet). Submit your repository link.",
        7,
        True,
    ),
    AssignmentSpec(
        "Design a Normalized Schema",
        "Design and implement models for a simple blogging platform: Author, Post, Tag (many-to-many "
        "with Post), and Comment (foreign key to Post). Include at least one custom Manager method "
        "(e.g. Post.objects.published()). Submit your models.py, your generated migration files, and "
        "a short ER-diagram sketch (image or text description) of the relationships.",
        10,
        True,
    ),
    AssignmentSpec(
        "Add JWT Auth to Your API",
        "Add djangorestframework-simplejwt to a Django REST Framework project of your choice (your own "
        "or the one from the DRF section). Implement /api/token/ and /api/token/refresh/ endpoints, "
        "and protect at least one existing endpoint so it returns 401 without a valid access token. "
        "Submit your repository link along with a Postman or curl transcript showing a full login flow.",
        10,
        True,
    ),
    AssignmentSpec(
        "Build a Custom Admin Dashboard",
        "Register at least three related models in the Django admin. Customize list_display, "
        "list_filter, and search_fields for each, add one custom admin action (e.g. 'mark selected as "
        "archived'), and add an inline editor for at least one related model. Submit your admin.py "
        "and a short screen recording or screenshots of the resulting admin pages.",
        7,
        True,
    ),
    AssignmentSpec(
        "Ship a Versioned Public API",
        "Build a read-only, versioned REST API (/api/v1/courses/) exposing a Course-like resource with "
        "list, retrieve, filtering, and pagination. Document it with drf-spectacular and include a "
        "working Swagger UI route. Submit your repository link plus the live (or local) Swagger URL.",
        14,
        True,
    ),
    AssignmentSpec(
        "Add a Scheduled Digest Email Job",
        "Configure Celery and Redis in a Django project. Write a task that compiles a 'daily digest' "
        "summary (any dummy data is fine) and logs it as if it were being emailed. Schedule it to run "
        "every day at 8am using Celery Beat. Submit your celery.py, tasks.py, and beat schedule config, "
        "plus a log excerpt showing the task actually running.",
        10,
        True,
    ),
    AssignmentSpec(
        "Reach 90% Coverage on Your Capstone",
        "Write pytest-django tests for a project of your choice covering models, at least one view, "
        "and one edge case (e.g. invalid input). Run coverage.py and reach at least 90% coverage on the "
        "files you tested. Submit your test files and a screenshot or text output of the coverage report.",
        10,
        True,
    ),
    AssignmentSpec(
        "Ship a Zero-Downtime Deploy Pipeline",
        "Containerize a Django project with a multi-stage Dockerfile, add a docker-compose.yml running "
        "web, db, and redis services, and put Gunicorn behind an NGINX reverse proxy. Submit your "
        "Dockerfile, docker-compose.yml, and NGINX config, plus a short write-up of your rollout strategy.",
        14,
        True,
    ),
    AssignmentSpec(
        "Add Caching and Signals to Your Capstone",
        "Add Redis-backed caching to at least one expensive view or queryset in a project of your "
        "choice, with a clear cache-invalidation strategy. Add one Django signal handler (e.g. "
        "invalidate the cache on post_save). Submit your code changes plus a short explanation of your "
        "invalidation strategy and why you chose it.",
        10,
        True,
    ),
    AssignmentSpec(
        "Submit Your Enterprise LMS Capstone",
        "Submit your completed capstone: an LMS with authentication and roles, a course catalog API, a "
        "checkout/payment flow (a sandboxed/mock gateway is fine), certificate generation on course "
        "completion, at least one background job, a test suite, and a working Docker-based deployment "
        "setup. Submit your repository link and a short demo video or write-up walking through each "
        "requirement.",
        21,
        False,
    ),
]


# ---------------------------------------------------------------------------
# Coding exercises — a handful of sections get a judged Python exercise.
# section_index refers to the 0-based position in SECTIONS.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TestCaseSpec:
    input: str
    expected_output: str
    is_hidden: bool
    weight: int = 1


@dataclass(frozen=True)
class CodingExerciseSpec:
    section_index: int
    title: str
    prompt: str
    starter_code: str
    test_cases: list[TestCaseSpec]


CODING_EXERCISES: list[CodingExerciseSpec] = [
    CodingExerciseSpec(
        1,
        "FizzBuzz with a Twist",
        "Read an integer n from stdin. Print the numbers 1..n, one per line, except: print 'Fizz' "
        "for multiples of 3, 'Buzz' for multiples of 5, and 'FizzBuzz' for multiples of both.",
        "n = int(input())\n# TODO: implement FizzBuzz and print each result on its own line\n",
        [
            TestCaseSpec(
                "15\n",
                "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n",
                False,
                1,
            ),
            TestCaseSpec("3\n", "1\n2\nFizz\n", True, 1),
        ],
    ),
    CodingExerciseSpec(
        3,
        "Group and Total Orders",
        "Read an integer n, then n lines each formatted as '<customer> <amount>'. Print each unique "
        "customer's running total, in the order that customer first appeared, formatted as "
        "'<customer>: <total>'.",
        "n = int(input())\n# TODO: read n 'customer amount' lines and print grouped totals\n",
        [
            TestCaseSpec(
                "4\nalice 10\nbob 5\nalice 3\nbob 2\n",
                "alice: 13\nbob: 7\n",
                False,
                1,
            ),
            TestCaseSpec("2\ncarol 100\ncarol 50\n", "carol: 150\n", True, 1),
        ],
    ),
    CodingExerciseSpec(
        6,
        "Paginate a List",
        "Read a line with two integers n and page_size, then a line of n space-separated integers. "
        "Print only the first page (the first page_size items), comma-separated with no trailing comma.",
        "n, page_size = map(int, input().split())\nitems = list(map(int, input().split()))\n# TODO: print the first page, comma-separated\n",
        [
            TestCaseSpec("7 3\n10 20 30 40 50 60 70\n", "10,20,30", False, 1),
            TestCaseSpec("2 5\n1 2\n", "1,2", True, 1),
        ],
    ),
    CodingExerciseSpec(
        7,
        "Task Queue Simulation",
        "Read an integer n, then n commands, each either 'ENQUEUE <task>' or 'RUN'. Maintain a FIFO "
        "queue: 'ENQUEUE <task>' adds a task to the back; 'RUN' removes and prints the task at the "
        "front, or prints 'EMPTY' if the queue has nothing to run.",
        "n = int(input())\n# TODO: process n commands against a FIFO queue\n",
        [
            TestCaseSpec(
                "5\nENQUEUE send_email\nENQUEUE generate_report\nRUN\nRUN\nRUN\n",
                "send_email\ngenerate_report\nEMPTY\n",
                False,
                1,
            ),
            TestCaseSpec("2\nENQUEUE ping\nRUN\n", "ping\n", True, 1),
        ],
    ),
    CodingExerciseSpec(
        8,
        "Assert Runner",
        "Read an integer n, then n lines each with two integers 'expected actual'. For each line, "
        "print 'PASS' if they're equal, otherwise 'FAIL'.",
        "n = int(input())\n# TODO: compare expected vs actual for each of n lines\n",
        [
            TestCaseSpec("3\n5 5\n2 3\n10 10\n", "PASS\nFAIL\nPASS\n", False, 1),
            TestCaseSpec("1\n7 8\n", "FAIL\n", True, 1),
        ],
    ),
    CodingExerciseSpec(
        11,
        "Certificate ID Generator",
        "Read a student's full name on the first line and a course code on the second line. Print a "
        "certificate ID formatted as 'CERT-<COURSE_CODE>-<INITIALS>', where INITIALS is the uppercase "
        "first letter of each word in the name, in order.",
        "name = input()\ncourse_code = input()\n# TODO: print the formatted certificate ID\n",
        [
            TestCaseSpec("Ada Lovelace\nDJANGO101\n", "CERT-DJANGO101-AL\n", False, 1),
            TestCaseSpec("Grace Hopper\nENTERPRISE9\n", "CERT-ENTERPRISE9-GH\n", True, 1),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Reviews (student -> course feedback)
# ---------------------------------------------------------------------------

REVIEWS: list[tuple[int, str]] = [
    (5, "The capstone project alone is worth the price. I went in only knowing basic Python and came out having deployed a real API with Docker."),
    (5, "Best Django course I've taken. The section quizzes actually made me go back and re-watch lessons instead of just clicking through."),
    (4, "Really solid, dense course. The Celery section moved a bit fast for me but the practice exercises helped it click."),
    (5, "I use the JWT auth lesson almost verbatim in my job now. Explains the 'why' behind each decision, not just the 'how'."),
    (5, "Finally a course that treats testing as a first-class citizen instead of an afterthought tacked on at the end."),
    (4, "Great content overall. Would love an even deeper dive into CQRS in a follow-up course."),
    (5, "The Django admin section alone saved me hours at work. Customizing list_display and admin actions is something I use weekly now."),
    (5, "Went from zero Django knowledge to confidently shipping a DRF API in about six weeks of evening study."),
    (3, "Good course but some sections assume a bit more prior Python knowledge than advertised. Still learned a lot."),
    (5, "The enterprise architecture section is what sets this apart from every other Django course out there."),
    (5, "Loved that every section ends with a real assignment, not just multiple choice. Forces you to actually build."),
    (4, "Clear explanations throughout. The deployment section could use a bit more on managed hosting options, but Docker coverage is excellent."),
    (5, "This is the course I wish existed when I started learning Django three years ago."),
    (5, "The instructor clearly explains not just Django but how to think about backend architecture in general."),
    (4, "Solid from start to finish. The pacing in the ORM section was perfect for me as someone new to SQL concepts."),
    (5, "Got the certificate, put it on LinkedIn, and had two recruiters mention it within the week."),
    (5, "The coding exercises with hidden test cases were a great touch — felt like a real technical interview."),
    (4, "Comprehensive and well structured. Wish there was a bonus section on GraphQL, but that's a minor nitpick."),
    (5, "Watching the capstone come together across sections instead of being a separate bolt-on project was genuinely well designed."),
    (5, "Worth every dollar. I'd happily pay double for the depth of the enterprise architecture and DRF sections."),
]


# ---------------------------------------------------------------------------
# Name pools for generating realistic (non-Faker) student identities.
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason", "Isabella", "Lucas",
    "Mia", "Elijah", "Amelia", "James", "Harper", "Benjamin", "Evelyn", "Henry", "Abigail", "Alexander",
    "Emily", "Michael", "Elizabeth", "Daniel", "Sofia", "Matthew", "Ella", "Jackson", "Grace", "Sebastian",
    "Chloe", "David", "Victoria", "Joseph", "Aria", "Samuel", "Scarlett", "Owen", "Zoey", "Wyatt",
    "Layla", "Gabriel", "Lily", "Anthony", "Nora", "Dylan", "Hannah", "Leo", "Aaliyah", "Julian",
    "Amara", "Kai", "Priya", "Diego", "Fatima", "Hiroshi", "Ingrid", "Kwame", "Mei", "Santiago",
    "Nadia", "Omar", "Freya", "Rohan", "Yuki", "Zainab", "Andres", "Chidi", "Elena", "Farhan",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Okafor", "Kim", "Patel", "Singh", "Diallo", "Tanaka", "Kowalski", "Mensah", "Haddad", "Popescu",
    "Ivanov", "Chowdhury", "Osei", "Delgado", "Ferreira", "Novak", "Abara", "Yamamoto", "Costa", "Berhane",
]
