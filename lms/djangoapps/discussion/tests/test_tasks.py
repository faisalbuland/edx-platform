import ddt
import json
from mock import patch, Mock


from lms.djangoapps.discussion.tasks import send_ace_message
from lms.djangoapps.django_comment_client.tests.utils import ForumsEnableMixin
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from django_comment_common.models import (
    CourseDiscussionSettings,
    ForumsConfig,
    FORUM_ROLE_STUDENT,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def make_mock_response(*thread_ids):
    def mock_response(*args, **kwargs):
        collection = [
            {'id': thread_id} for thread_id in thread_ids
        ]
        data = {
            'collection': collection,
            'page': 1,
            'num_pages': 1,
            'thread_count': len(collection)
        }
        return Mock(status_code=200, text=json.dumps(data), json=Mock(return_value=data))

    return mock_response


@ddt.ddt
class TaskTestCase(ModuleStoreTestCase):

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(TaskTestCase, self).setUp()

        self.course = CourseFactory.create(discussion_topics={'dummy discussion': {'id': 'dummy_discussion_id'}})

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):

            self.thread_author = UserFactory(
                username='thread_user',
                password='password',
                email='email'
            )
            self.comment_author = UserFactory(
                username='comment_user',
                password='password',
                email='email'
            )

            CourseEnrollmentFactory(
                user=self.thread_author,
                course_id=self.course.id
            )
            CourseEnrollmentFactory(
                user=self.comment_author,
                course_id=self.course.id
            )

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

    @ddt.data(True, False)
    @patch('student.models.cc.User.from_django_user')
    @patch('edx_ace.send')
    def test_send_message_2(self, mock_ace_send, mock_from_django_user, is_user_subscribed):
        with patch('student.models.cc.User.subscribed_threads', return_value=is_user_subscribed):
                send_ace_message(
                    thread_id='dummy_discussion_id',
                    thread_author_id=self.thread_author.id,
                    comment_author_id=self.comment_author.id,
                    course_id=self.course.id
                )
                with patch('lms.djangoapps.discussion.tasks._build_email_context') as build_email_context_mock:
                    if is_user_subscribed:
                        self.assertTrue(mock_ace_send.called)
                        build_email_context_mock.assert_called_once_with(self.comment_author, 'dummy_discussion_id')
                    else:
                        self.assertFalse(mock_ace_send.called)

    @ddt.data(True, False)
    @patch('requests.request', autospec=True)
    @patch('edx_ace.send')
    def test_send_message(self, user_subscribed, mock_request, mock_ace_send):
        if user_subscribed:
            mock_request.side_effect = make_mock_response('dummy_discussion_id')
        else:
            mock_request.side_effect = make_mock_response()

        send_ace_message(
            thread_id='dummy_discussion_id',
            thread_author_id=self.thread_author.id,
            comment_author_id=self.comment_author.id,
            course_id=self.course.id
        )

        if user_subscribed:
            self.assertTrue(mock_ace_send.called)
            # build_email_context_mock.assert_called_once_with(self.comment_author, 'dummy_discussion_id')
        else:
            self.assertFalse(mock_ace_send.called)
