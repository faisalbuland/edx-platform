from django.test.client import Client
from mock import patch
from nose.tools import assert_true

from lms.djangoapps.discussion.tasks import send_ace_message
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from django_comment_common.models import (
    CourseDiscussionSettings,
    ForumsConfig,
    FORUM_ROLE_STUDENT,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class BlaTestCase(ModuleStoreTestCase):

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(BlaTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.thread_user = UserFactory(
            username='thread_user',
            password='password',
            email='email'
        )
        self.comment_user = UserFactory(
            username='comment_user',
            password='password',
            email='email'
        )

        CourseEnrollmentFactory(
            user=self.thread_user,
            course_id=self.course.id
        )
        CourseEnrollmentFactory(
            user=self.comment_user,
            course_id=self.course.id
        )

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the student
            self.student = UserFactory(username=uname, password=password, email=email)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Log the student in
            self.client = Client()
            assert_true(self.client.login(username=uname, password=password))

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

    @patch('student.models.cc.User.from_django_user')
    @patch('student.models.cc.User.subscribed_threads')
    def test_send_message(self, mock_threads, mock_from_django_user):
        send_ace_message(
            thread_id='thread_id',
            thread_user_id=self.thread_user.id,
            comment_user_id=self.comment_user.id,
            course_id=self.course.id
        )
