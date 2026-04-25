"""Celery application factory — broker/backend wired from env."""

from celery import Celery

celery_app = Celery("ucar")
