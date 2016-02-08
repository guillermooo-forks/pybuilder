#   -*- coding: utf-8 -*-
#
#   This file is part of PyBuilder
#
#   Copyright 2011-2015 PyBuilder Team
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import unittest
import sys

try:
    from unittest import skipIf
except ImportError:
    def skipIf(*args, **kwargs):
        def inner(test):
            def innermost(*args, **kwargs):
                if sys.platform == 'win32':
                    return
                test(*args, **kwargs)
            innermost.__name__ = test.__name__
            return innermost
        return inner

from mock import patch, Mock, call

from pybuilder.core import Project
from pybuilder.errors import BuildFailedException
from pybuilder.plugins.python.cram_plugin import (
    _cram_command_for,
    _find_files,
    _report_file,
    run_cram_tests,
)


class CramPluginTests(unittest.TestCase):

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    def test_command_respects_no_verbose(self):
        project = Project('.')
        project.set_property('verbose', False)
        expected = ['cram', '-E']
        received = _cram_command_for(project)
        self.assertEquals(expected, received)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    def test_command_respects_verbose(self):
        project = Project('.')
        project.set_property('verbose', True)
        expected = ['cram', '-E', '--verbose']
        received = _cram_command_for(project)
        self.assertEquals(expected, received)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    @patch('pybuilder.plugins.python.cram_plugin.discover_files_matching')
    def test_find_files(self, discover_mock):
        project = Project('.')
        project.set_property('dir_source_cmdlinetest', '/any/dir')
        project.set_property('cram_test_file_glob', '*.t')
        expected = ['/any/dir/test.cram']
        discover_mock.return_value = expected
        received = _find_files(project)
        self.assertEquals(expected, received)
        discover_mock.assert_called_once_with('/any/dir', '*.t')

    def test_report(self):
        project = Project('.')
        project.set_property('dir_reports', '/any/dir')
        expected = './any/dir/cram.err'
        received = _report_file(project)
        self.assertEquals(expected, received)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    @patch('pybuilder.plugins.python.cram_plugin._cram_command_for')
    @patch('pybuilder.plugins.python.cram_plugin._find_files')
    @patch('pybuilder.plugins.python.cram_plugin._report_file')
    @patch('os.environ')
    @patch('pybuilder.plugins.python.cram_plugin.read_file')
    @patch('pybuilder.plugins.python.cram_plugin.execute_command')
    def test_running_plugin_cram_from_target(self,
                                             execute_mock,
                                             read_file_mock,
                                             os_mock,
                                             report_mock,
                                             find_files_mock,
                                             command_mock
                                             ):
        project = Project('.')
        project.set_property('cram_run_test_from_target', True)
        project.set_property('dir_dist', 'python')
        project.set_property('dir_dist_scripts', 'scripts')
        project.set_property('verbose', False)
        logger = Mock()

        command_mock.return_value = ['cram']
        find_files_mock.return_value = ['test1.cram', 'test2.cram']
        report_mock.return_value = 'report_file'
        os_mock.copy.return_value = {}
        read_file_mock.return_value = ['test failes for file', '# results']
        execute_mock.return_value = 0

        run_cram_tests(project, logger)
        execute_mock.assert_called_once_with(
            ['cram', 'test1.cram', 'test2.cram'], 'report_file',
            error_file_name='report_file',
            env={'PYTHONPATH': './python:', 'PATH': './python/scripts:'}
        )
        expected_info_calls = [call('Running Cram command line tests'),
                               call('Cram tests were fine'),
                               call('results'),
                               ]
        self.assertEquals(expected_info_calls, logger.info.call_args_list)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    @patch('pybuilder.plugins.python.cram_plugin._cram_command_for')
    @patch('pybuilder.plugins.python.cram_plugin._find_files')
    @patch('pybuilder.plugins.python.cram_plugin._report_file')
    @patch('os.environ')
    @patch('pybuilder.plugins.python.cram_plugin.read_file')
    @patch('pybuilder.plugins.python.cram_plugin.execute_command')
    def test_running_plugin_from_scripts(self,
                                         execute_mock,
                                         read_file_mock,
                                         os_mock,
                                         report_mock,
                                         find_files_mock,
                                         command_mock
                                         ):
        project = Project('.')
        project.set_property('cram_run_test_from_target', False)
        project.set_property('dir_source_main_python', 'python')
        project.set_property('dir_source_main_scripts', 'scripts')
        project.set_property('verbose', False)
        logger = Mock()

        command_mock.return_value = ['cram']
        find_files_mock.return_value = ['test1.cram', 'test2.cram']
        report_mock.return_value = 'report_file'
        os_mock.copy.return_value = {}
        read_file_mock.return_value = ['test failes for file', '# results']
        execute_mock.return_value = 0

        run_cram_tests(project, logger)
        execute_mock.assert_called_once_with(
            ['cram', 'test1.cram', 'test2.cram'], 'report_file',
            error_file_name='report_file',
            env={'PYTHONPATH': './python:', 'PATH': './scripts:'}
        )
        expected_info_calls = [call('Running Cram command line tests'),
                               call('Cram tests were fine'),
                               call('results'),
                               ]
        self.assertEquals(expected_info_calls, logger.info.call_args_list)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    @patch('pybuilder.plugins.python.cram_plugin._cram_command_for')
    @patch('pybuilder.plugins.python.cram_plugin._find_files')
    @patch('pybuilder.plugins.python.cram_plugin._report_file')
    @patch('os.environ')
    @patch('pybuilder.plugins.python.cram_plugin.read_file')
    @patch('pybuilder.plugins.python.cram_plugin.execute_command')
    def test_running_plugin_fails(self,
                                  execute_mock,
                                  read_file_mock,
                                  os_mock,
                                  report_mock,
                                  find_files_mock,
                                  command_mock
                                  ):
        project = Project('.')
        project.set_property('verbose', False)
        project.set_property('dir_source_main_python', 'python')
        project.set_property('dir_source_main_scripts', 'scripts')
        logger = Mock()

        command_mock.return_value = ['cram']
        find_files_mock.return_value = ['test1.cram', 'test2.cram']
        report_mock.return_value = 'report_file'
        os_mock.copy.return_value = {}
        read_file_mock.return_value = ['test failes for file', '# results']
        execute_mock.return_value = 1

        self.assertRaises(
            BuildFailedException, run_cram_tests, project, logger)
        execute_mock.assert_called_once_with(
            ['cram', 'test1.cram', 'test2.cram'], 'report_file',
            error_file_name='report_file',
            env={'PYTHONPATH': './python:', 'PATH': './scripts:'}
        )
        expected_info_calls = [call('Running Cram command line tests'),
                               ]
        expected_error_calls = [call('Cram tests failed!'),
                                call('results'),
                                call("See: 'report_file' for details"),
                                ]
        self.assertEquals(expected_info_calls, logger.info.call_args_list)
        self.assertEquals(expected_error_calls, logger.error.call_args_list)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    @patch('pybuilder.plugins.python.cram_plugin._cram_command_for')
    @patch('pybuilder.plugins.python.cram_plugin._find_files')
    @patch('pybuilder.plugins.python.cram_plugin._report_file')
    @patch('os.environ')
    @patch('pybuilder.plugins.python.cram_plugin.read_file')
    @patch('pybuilder.plugins.python.cram_plugin.execute_command')
    def test_running_plugin_fails_with_verbose(self,
                                               execute_mock,
                                               read_file_mock,
                                               os_mock,
                                               report_mock,
                                               find_files_mock,
                                               command_mock
                                               ):
        project = Project('.')
        project.set_property('verbose', True)
        project.set_property('dir_source_main_python', 'python')
        project.set_property('dir_source_main_scripts', 'scripts')
        logger = Mock()

        command_mock.return_value = ['cram']
        find_files_mock.return_value = ['test1.cram', 'test2.cram']
        report_mock.return_value = 'report_file'
        os_mock.copy.return_value = {}
        read_file_mock.return_value = ['test failes for file', '# results']
        execute_mock.return_value = 1

        self.assertRaises(
            BuildFailedException, run_cram_tests, project, logger)
        execute_mock.assert_called_once_with(
            ['cram', 'test1.cram', 'test2.cram'], 'report_file',
            error_file_name='report_file',
            env={'PYTHONPATH': './python:', 'PATH': './scripts:'}
        )
        expected_info_calls = [call('Running Cram command line tests'),
                               ]
        expected_error_calls = [call('Cram tests failed!'),
                                call('test failes for file'),
                                call('# results'),
                                call("See: 'report_file' for details"),
                                ]
        self.assertEquals(expected_info_calls, logger.info.call_args_list)
        self.assertEquals(expected_error_calls, logger.error.call_args_list)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    @patch('pybuilder.plugins.python.cram_plugin._cram_command_for')
    @patch('pybuilder.plugins.python.cram_plugin._find_files')
    @patch('pybuilder.plugins.python.cram_plugin._report_file')
    @patch('os.environ')
    @patch('pybuilder.plugins.python.cram_plugin.read_file')
    @patch('pybuilder.plugins.python.cram_plugin.execute_command')
    def test_running_plugin_no_failure_no_tests(self,
                                                execute_mock,
                                                read_file_mock,
                                                os_mock,
                                                report_mock,
                                                find_files_mock,
                                                command_mock
                                                ):
        project = Project('.')
        project.set_property('verbose', True)
        project.set_property('dir_source_main_python', 'python')
        project.set_property('dir_source_main_scripts', 'scripts')
        project.set_property("cram_fail_if_no_tests", False)
        logger = Mock()

        command_mock.return_value = ['cram']
        find_files_mock.return_value = []
        report_mock.return_value = 'report_file'
        os_mock.copy.return_value = {}
        read_file_mock.return_value = ['test failes for file', '# results']
        execute_mock.return_value = 1

        run_cram_tests(project, logger)

        execute_mock.assert_not_called()
        expected_info_calls = [call('Running Cram command line tests'),
                               ]
        self.assertEquals(expected_info_calls, logger.info.call_args_list)

    @skipIf(sys.platform == 'win32', 'because cram plugin does not work on Windows')
    @patch('pybuilder.plugins.python.cram_plugin._cram_command_for')
    @patch('pybuilder.plugins.python.cram_plugin._find_files')
    @patch('pybuilder.plugins.python.cram_plugin._report_file')
    @patch('os.environ')
    @patch('pybuilder.plugins.python.cram_plugin.read_file')
    @patch('pybuilder.plugins.python.cram_plugin.execute_command')
    def test_running_plugin_failure_no_tests(self,
                                             execute_mock,
                                             read_file_mock,
                                             os_mock,
                                             report_mock,
                                             find_files_mock,
                                             command_mock
                                             ):
        project = Project('.')
        project.set_property('verbose', True)
        project.set_property('dir_source_main_python', 'python')
        project.set_property('dir_source_main_scripts', 'scripts')
        project.set_property("cram_fail_if_no_tests", True)
        logger = Mock()

        command_mock.return_value = ['cram']
        find_files_mock.return_value = []
        report_mock.return_value = 'report_file'
        os_mock.copy.return_value = {}
        read_file_mock.return_value = ['test failes for file', '# results']
        execute_mock.return_value = 1

        self.assertRaises(
            BuildFailedException, run_cram_tests, project, logger)

        execute_mock.assert_not_called()
        expected_info_calls = [call('Running Cram command line tests'),
                               ]
        self.assertEquals(expected_info_calls, logger.info.call_args_list)
