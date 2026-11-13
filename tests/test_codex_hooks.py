"""Run with: python3 -m unittest discover -s tests -v"""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a


class CodexHooksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sessions = self.root / 'sessions'
        self.sessions.mkdir()
        self.patches = [
            patch.object(a, 'SESS_DIR', str(self.sessions)),
            patch.object(a, 'MGR_HOME', str(self.root)),
            patch.object(a, 'hook_from_managed_agent', return_value=False),
            patch.object(a, 'update_agent_info'),
            patch.object(a, 'collab_hook', return_value=False),
            patch.object(a, 'set_terminal_title'),
            patch.dict(os.environ, {'NIRENNE_AGENT_LEVEL': '2',
                                    'AGENT_SESSION_FILE': '/wrong/inherited.env'}),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def session(self, name='one', thread='thread-one', agent='Codex'):
        p = self.sessions / (name + '.env')
        p.write_text(f'ID={name}\nAGENT={agent}\nSTATUS=RUNNING\nPID={os.getpid()}\n'
                     f'DIRECTORY={self.root}\nAGENT_THREAD={thread}\nACTIVITY=\n')
        return str(p)

    def event(self, event, thread='thread-one', agent='codex', **extra):
        data = dict(hook_event_name=event, session_id=thread, cwd=str(self.root), **extra)
        with patch.object(sys, 'stdin', io.StringIO(json.dumps(data))):
            a.claude_hook(agent)

    def test_shared_service_lifecycle(self):
        path = self.session()
        other = self.session('two', 'thread-two')
        for event, expected in [('SessionStart', 'WAITING'),
                                ('UserPromptSubmit', 'WORKING'),
                                ('PermissionRequest', 'APPROVAL'),
                                ('PostToolUse', 'WORKING'), ('Stop', 'WAITING')]:
            self.event(event, prompt='Fix status')
            self.assertEqual(a.read_kv(path)['ACTIVITY'], expected)
            self.assertEqual(a.read_kv(other)['ACTIVITY'], '')
        self.assertTrue(a.read_kv(path)['WORK_START'])
        self.assertNotEqual(a.read_kv(path)['LAST_DURATION'], '')

    def test_first_event_binds_unique_candidate(self):
        path = self.session(thread='')
        self.event('UserPromptSubmit', prompt='Hello')
        self.assertEqual(a.read_kv(path)['AGENT_THREAD'], 'thread-one')
        self.assertEqual(a.read_kv(path)['ACTIVITY'], 'WORKING')

    def test_ambiguous_candidates_are_not_bound(self):
        paths = [self.session('one', ''), self.session('two', '')]
        self.event('UserPromptSubmit')
        for path in paths:
            self.assertEqual(a.read_kv(path)['AGENT_THREAD'], '')
            self.assertEqual(a.read_kv(path)['ACTIVITY'], '')

    def test_unmanaged_thread_does_not_change_bound_session(self):
        path = self.session()
        self.event('UserPromptSubmit', thread='unmanaged')
        self.assertEqual(a.read_kv(path)['ACTIVITY'], '')

    def test_missing_thread_does_not_bind(self):
        path = self.session(thread='')
        self.event('UserPromptSubmit', thread='')
        self.assertEqual(a.read_kv(path)['ACTIVITY'], '')

    def test_claude_still_rejects_unrelated_process(self):
        path = self.session(agent='Claude')
        with patch.dict(os.environ, {'AGENT_SESSION_FILE': path, 'NIRENNE_AGENT_LEVEL': '1'}):
            self.event('UserPromptSubmit', agent='claude')
        self.assertEqual(a.read_kv(path)['ACTIVITY'], '')


if __name__ == '__main__':
    unittest.main()
