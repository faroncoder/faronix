from django.shortcuts import render
from django.template.loader import render_to_string
from core.utils.middleware import get_debug_info
from django.conf import settings


# def tint_toggle(request):
#     # You can customize this logic as needed
#     return {"tintToggle": "tinted"}  # or 'untinted', or dynamic logic


# def render_modal_page(
#     request,
#     *,
#     partial_template,
#     modal_title,
#     page_template="core/base.html",
#     context=None
# ):
#     """
#     Render either:
#         - HTMX partial (for hx-get)
#         - or a full page with the modal open
#     """
#     context = context or {}
#     # Set tintToggle only if rendering a full page (not partial)
#     tintToggle = None
#     if not getattr(request, "htmx", False):
#         tintToggle = (
#             "untinted" if "untinted" in request.GET.get("tint", "") else "tinted"
#         )
#         context["tintToggle"] = tintToggle

#     if getattr(request, "htmx", False):
#         return render(request, partial_template, context)

#     page_ctx = {
#         **context,
#         "modal_active": True,
#         "modal_title": modal_title,
#         "tintToggle": "tinted" if tintToggle == "tinted" else "untinted",
#         "modal_content": render_to_string(
#             partial_template, context, request=request
#         ),  # injected into #hxload-doc in modal_shell
#     }
#     return render(request, page_template, page_ctx)


def global_vars(request):

    return {
        "company": "SignaVision Solutions Inc.",
        "url": "https://lti.signavision.ca",
        "email": "info@signavision.ca",
        "address": "1867 Yonge Street, Suite 906",
        "city": "Toronto",
        "prov": "Ontario",
        "pcode": "M4S 1Y5",
        "staff": [
            "executive_director",
            "project_director",
            "manager",
            "senior_developer",
            "developer",
            "senior_graphic_developer",
            "graphic_developer",
            "executive_assistant",
        ],
        "missions": [
            "Innovation",
            "Empowerment",
            "Collaboration",
            "Advocacy",
            "Respect",
        ],
        "services": [
            "training",
            "research",
            "resource_development",
            "networking",
            "professional_development",
            "conference",
        ],
        "type_of_business": "Profit-Based",
        "events": [
            "workshop",
            "annual_conference",
            "targeted_training",
            "webinar",
            "learners_event",
            "fund_raising_event",
        ],
        "social_media": {
            "facebook": "https://www.facebook.com/SignaVision",
            "linkedin": "",
        },
        "htmx_defaults": {"target": "#main", "trigger": "click", "push_url": False},
        ### SITE BEGIN
        "menu": {
            "site": [
                {"label": "Home", "url_name": "core:index", "fa_icon": "fas fa-home"},
                {
                    "label": "About Us",
                    "url_name": "core:about",
                    "fa_icon": "fas fa-info-circle",
                },
                {
                    "label": "Events",
                    "url_name": "core:event",
                    "fa_icon": "fas fa-calendar-alt",
                },
                {
                    "label": "Support",
                    "url_name": "core:resource",
                    "fa_icon": "fas fa-hands-helping",
                },
                {
                    "label": "Contact",
                    "url_name": "core:contact",
                    "fa_icon": "fas fa-envelope",
                },
            ],
            "Services": [
                {
                    "label": "Webinar Sessions",
                    "url_name": "core:webinars",
                    "fa_icon": "fas fa-video",
                },
                {
                    "label": "Digital Library",
                    "url_name": "core:oalcf",
                    "fa_icon": "fas fa-book",
                },
                {
                    "label": "Conference",
                    "url_name": "core:conferences",
                    "fa_icon": "fas fa-users",
                },
                {
                    "label": "Curriculum",
                    "url_name": "core:curriculum",
                    "fa_icon": "fas fa-book-open",
                },
                {
                    "label": "Articles",
                    "url_name": "core:articles",
                    "fa_icon": "fas fa-newspaper",
                },
                {
                    "label": "Knowledgebase",
                    "url_name": "core:kbpanel",
                    "fa_icon": "fas fa-lightbulb",
                },
                {
                    "label": "Knowledgebase Default",
                    "url_name": "core:kbdefault",
                    "fa_icon": "fas fa-lightbulb",
                },
            ],
            "Networks": [
                {
                    "label": "Ontario Ministry",
                    "url_name": "core:ministry",
                    "fa_icon": "fas fa-university",
                },
                {
                    "label": "Communities",
                    "url_name": "core:communities",
                    "fa_icon": "fas fa-users",
                },
                {
                    "label": "Programs",
                    "url_name": "core:programs",
                    "fa_icon": "fas fa-th-list",
                },
                {
                    "label": "Partners",
                    "url_name": "core:partners",
                    "fa_icon": "fas fa-handshake",
                },
                {
                    "label": "News Updates",
                    "url_name": "core:news",
                    "fa_icon": "fas fa-bullhorn",
                },
            ],
            "online_platform": [
                {
                    "label": "Canvas",
                    "url_name": "core:canvas",
                    "fa_icon": "fas fa-paint-brush",
                },
                {
                    "label": "S5 DLI Portal",
                    "url_name": "core:platform",
                    "fa_icon": "fas fa-network-wired",
                },
                {
                    "label": "Account",
                    "url_name": "core:accountview",
                    "fa_icon": "fas fa-user-cog",
                },
            ],
        },
        ### SITE END
        "resources_section": {
            "title": "Support Services We Provide",
            "items": [
                {
                    "title": "Professional Development",
                    "description": "Annual conference and Webinar sessions",
                    "image": "/static/img/1.jpg",
                    "url_name": "conference",
                    "slug": None,
                },
                {
                    "title": "Resource Development",
                    "description": "Developing learning activities and materials",
                    "image": "/static/img/2.jpg",
                    "url_name": "contact",
                    "slug": None,
                },
                {
                    "title": "Networking",
                    "description": "Referral and connecting all programs",
                    "image": "/static/img/3.jpg",
                    "url_name": "oalcf",
                    "slug": None,
                },
                {
                    "title": "Training Programs",
                    "description": "Various educational resources",
                    "image": "/static/img/4.jpg",
                    "url_name": "event",
                    "slug": None,
                },
                {
                    "title": "Referral",
                    "description": "Connecting your learners to any needed programs",
                    "image": "/static/img/5.jpg",
                    "url_name": "about",
                    "slug": None,
                },
                {
                    "title": "Coming Soon!",
                    "description": "Member Portal to access all materials",
                    "image": "/static/img/6.jpg",
                    "url_name": None,
                    "slug": None,
                },
            ],
        },
        "knowledgebase": {
            "featured": [
                {
                    "slug": "most-used-strategies",
                    "title": "Most-Used Strategies",
                    "description": "Popular literacy strategies among educators",
                    "count": 10,
                    "kind": "strategies",
                    "icon": "book-open",
                    "color_class": "text-primary",
                },
                {
                    "slug": "top-rated-materials",
                    "title": "Top-Rated Materials",
                    "description": "Educator-reviewed literacy tools and activities",
                    "count": 10,
                    "kind": "materials",
                    "icon": "star",
                    "color_class": "text-secondary",
                },
                {
                    "slug": "classroom-policies",
                    "title": "Classroom Policies",
                    "description": "Assessment, inclusion, and accessibility guidelines",
                    "count": 7,
                    "kind": "articles",
                    "icon": "clipboard-check",
                    "color_class": "text-teal",
                },
            ],
            "collections": [
                {
                    "slug": "early-literacy",
                    "title": "Early Literacy",
                    "description": "Phonemic awareness, letter-sound knowledge, and emergent reading activities",
                    "count": 6,
                    "kind": "articles",
                    "icon": "abc",
                    "color_class": "text-success",
                },
                {
                    "slug": "assessment-tools",
                    "title": "Assessment Tools",
                    "description": "Checklists, rubrics, and diagnostic tools",
                    "count": 4,
                    "kind": "tools",
                    "icon": "clipboard",
                    "color_class": "text-warning",
                },
                {
                    "slug": "family-engagement",
                    "title": "Family Engagement",
                    "description": "Resources to support home-school connections",
                    "count": 3,
                    "kind": "guides",
                    "icon": "home",
                    "color_class": "text-orange",
                },
                {
                    "slug": "inclusive-teaching",
                    "title": "Inclusive Teaching",
                    "description": "Multilingual, culturally responsive, and Deaf-inclusive approaches",
                    "count": 5,
                    "kind": "articles",
                    "icon": "users",
                    "color_class": "text-indigo",
                },
                {
                    "slug": "digital-literacy",
                    "title": "Digital Literacy",
                    "description": "Tech-integrated reading and writing supports",
                    "count": 2,
                    "kind": "articles",
                    "icon": "tablet",
                    "color_class": "text-blue",
                },
                {
                    "slug": "professional-growth",
                    "title": "Professional Growth",
                    "description": "Training, webinars, and self-paced learning",
                    "count": 3,
                    "kind": "development",
                    "icon": "trending-up",
                    "color_class": "text-purple",
                },
            ],
        },
    }


def debug_to_browser(request):
    """
    Inject debug info for browser console if DEBUG is True and info is present.
    """
    if getattr(settings, "DEBUG", False):
        debug_info = get_debug_info()
        if debug_info:
            return {"debug_info": debug_info}
    return {}
