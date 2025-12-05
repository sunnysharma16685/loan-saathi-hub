from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7  # default for generic pages

    def items(self):
        return [
            "index",
            "register",
            "login",

            # Public feature pages
            "loan_request",
            "support",
            "complaint",
            "feedback",
            "advertise",

            # Footer informational pages
            "about",
            "terms",
            "privacy",
            "faq",
            "contact",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        """ Give higher priority to business-critical pages """
        high_priority = {"home", "loan_request", "about", "contact"}
        if item in high_priority:
            return 0.9
        return 0.7
