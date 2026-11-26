import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from editing_runtime import EditingRuntime

class EditingRuntimeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.runtime=EditingRuntime(self.root/'machine');self.runtime.root=self.root/'engine'
 def installed(self):
  package=self.runtime.root/'node_modules/openfilm';(package/'studio/ui/dist').mkdir(parents=True)
  (package/'package.json').write_text(json.dumps({'version':'0.4.1'}))
  (package/'studio/client.mjs').touch();(package/'studio/ui/dist/index.html').touch()
 def test_missing_tools_are_reported_without_installing(self):
  with patch('editing_runtime.shutil.which',return_value=None):
   result=self.runtime.status();self.assertFalse(result['ready']);self.assertFalse(result['can_prepare'])
   with self.assertRaises(ValueError):self.runtime.prepare()
  self.assertFalse(self.runtime.root.exists())
 def test_existing_openfilm_reuses_package_and_browser_installer(self):
  self.installed();commands=[]
  with patch.object(self.runtime,'status',return_value={'components':[{'id':'openfilm','ready':True}]}),patch.object(self.runtime,'_run',side_effect=lambda args,output:commands.append(args)),patch('editing_runtime.shutil.which',return_value='node'):
   self.runtime._prepare()
  self.assertEqual(len(commands),1);self.assertEqual(commands[0][-2:],['install','chromium-headless-shell'])
  self.assertEqual(self.runtime.phase,'complete')
  self.assertEqual(self.runtime.environment()['SHORT_DRAMA_OPENFILM_HOME'],str(self.runtime.root))
 def test_install_uses_pinned_package_then_upstream_browser_installer(self):
  commands=[]
  with patch.object(self.runtime,'status',return_value={'components':[{'id':'openfilm','ready':False}]}),patch.object(self.runtime,'npm_command',return_value=['node','npm-cli.js']),patch.object(self.runtime,'_run',side_effect=lambda args,output:commands.append(args)),patch('editing_runtime.shutil.which',return_value='node'):
   self.runtime._prepare()
  self.assertIn('openfilm@0.4.1',commands[0]);self.assertIn(str(self.runtime.root),commands[0])
  self.assertEqual(len(commands),2);self.assertEqual(self.runtime.phase,'complete')
 def test_failure_is_recoverable_without_false_success(self):
  with patch.object(self.runtime,'status',return_value={'components':[{'id':'openfilm','ready':True}]}),patch.object(self.runtime,'_run',side_effect=OSError('offline')),patch('editing_runtime.shutil.which',return_value='node'):
   self.runtime._prepare()
  self.assertEqual(self.runtime.phase,'failed');self.assertIn('重试',self.runtime.error)

if __name__=='__main__':unittest.main()
