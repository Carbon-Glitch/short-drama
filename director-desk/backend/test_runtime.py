import json
import os
from pathlib import Path
import tempfile
import unittest
from runtime import Runtime,protect
from production import Production
from library import Library
from server import AppServer
from urllib.request import Request,urlopen
import threading
from unittest.mock import patch

@unittest.skipUnless(os.name=='nt','Windows DPAPI')
class RuntimeTests(unittest.TestCase):
    def test_seedance_environment_includes_installed_duration_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime=Runtime(tmp)
            runtime.save({'provider':'seedance','model':'fixture-seedance-2.5','api_key':'fixture-secret'})
            env=runtime.environment('seedance')
            self.assertEqual(env['SEEDANCE_MODEL'],'fixture-seedance-2.5')
            self.assertEqual(env['SEEDANCE_MIN_DURATION'],'4');self.assertEqual(env['SEEDANCE_MAX_DURATION'],'30')
            self.assertIn('adaptive',env['SEEDANCE_ALLOWED_RATIOS'].split(','))
    def test_encrypted_configuration_preserves_key_and_custom_adapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);custom={'command':['custom-tool']}
            (home/'adapters.json').write_text(json.dumps({'adapters':{'existing':custom}}))
            runtime=Runtime(home)
            public=runtime.save({'provider':'minimax-h3','model':'fixture-model','api_key':'fixture-secret'})
            self.assertNotIn('fixture-secret',runtime.file.read_text())
            self.assertNotIn('key"',json.dumps(public))
            self.assertTrue(public['providers'][0]['key_configured'])
            runtime.save({'provider':'minimax-h3','model':'fixture-updated','api_key':''})
            env=runtime.environment('minimax-h3')
            self.assertEqual(env['MINIMAX_API_KEY'],'fixture-secret')
            self.assertEqual(env['MINIMAX_VIDEO_MODEL'],'fixture-updated')
            config=json.loads((home/'adapters.json').read_text())
            self.assertEqual(config['adapters']['existing'],custom)
            self.assertEqual(config['adapters']['director-minimax-h3']['kind'],'video')
            self.assertEqual(protect(protect('测试密钥'),True),'测试密钥')

    def test_frozen_provider_preserves_confirmed_model_and_encrypted_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            library=Library(tmp);runtime=Runtime(library.home)
            runtime.save({'provider':'minimax-h3','model':'original-model','api_key':'original-test-key'})
            production=Production(library);adapter='director-minimax-h3'
            revision=production.service_revision(production.service_details(adapter))
            snapshot=production.freeze_service('local-freeze-test',adapter,revision)
            runtime.save({'provider':'minimax-h3','model':'changed-model','api_key':'changed-test-key'})
            frozen=Runtime(snapshot.parent).environment('minimax-h3')
            self.assertEqual(frozen['MINIMAX_VIDEO_MODEL'],'original-model')
            self.assertEqual(frozen['MINIMAX_API_KEY'],'original-test-key')
            self.assertNotIn('original-test-key',(snapshot.parent/'runtime-settings.json').read_text())

    def test_frozen_seedance_profile_does_not_reread_updated_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            library=Library(tmp);runtime=Runtime(library.home)
            runtime.save({'provider':'seedance','model':'fixed-model','api_key':'fixture-secret'})
            production=Production(library);adapter='director-seedance'
            revision=production.service_revision(production.service_details(adapter))
            snapshot=production.freeze_service('fixed-profile-test',adapter,revision)
            with patch('runtime.model_presets',side_effect=AssertionError('must use snapshot')):
                env=Runtime(snapshot.parent).environment('seedance')
            self.assertEqual(env['SEEDANCE_MAX_DURATION'],'30');self.assertEqual(env['SEEDANCE_MODEL'],'fixed-model')
            with patch('production.model_presets',return_value=[{'id':'seedance-2.5','choices':{'target_video_model':'seedance-2.5','native_duration_seconds':{'min':4,'max':12}}}]):
                with self.assertRaisesRegex(ValueError,'配置已改变'):production.freeze_service('not-confirmed',adapter,revision)

    def test_http_settings_publish_profile_without_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            server=AppServer(('127.0.0.1',0),Library(tmp))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            origin=f'http://127.0.0.1:{server.server_port}'
            try:
                request=Request(origin+'/api/runtime',data=json.dumps({'provider':'gpt-image-2','api_key':'fixture-secret'}).encode(),headers={'X-Director-Session':server.token,'Origin':origin})
                with urlopen(request) as response:result=json.load(response)
                self.assertTrue(result['providers'][0]['key_configured'])
                self.assertNotIn('fixture-secret',json.dumps(result))
                with urlopen(origin+'/api/generation-profiles') as response:profiles=json.load(response)
                self.assertEqual(profiles[0]['kind'],'image')
                self.assertEqual(profiles[0]['name'],'GPT Image')
            finally:
                server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
