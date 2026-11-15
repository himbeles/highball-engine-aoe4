#!/usr/bin/env python3
import hashlib,io,json,pathlib,struct,subprocess,sys,tarfile,tempfile,unittest
HERE=pathlib.Path(__file__).resolve().parents[1]
class Tools(unittest.TestCase):
    def command(self,tool,*args,ok=True):
        result=subprocess.run([sys.executable,str(HERE/tool),*map(str,args)],capture_output=True,text=True)
        self.assertEqual(result.returncode==0,ok,result.stdout+result.stderr)
        return result
    def test_profile_is_hash_bound_and_refuses_wrong_data_address(self):
        with tempfile.TemporaryDirectory() as root:
            root=pathlib.Path(root);exe=root/'RelicCardinal.exe';b=bytearray(1024)
            b[:2]=b'MZ';struct.pack_into('<I',b,60,128);b[128:132]=b'PE\0\0'
            struct.pack_into('<HH',b,132,0x8664,1);struct.pack_into('<H',b,148,240)
            struct.pack_into('<H',b,152,0x20b);struct.pack_into('<Q',b,176,0x140000000)
            b[392:400]=b'.data\0\0\0';struct.pack_into('<II',b,400,0x1000,0x2000)
            struct.pack_into('<I',b,428,0xc0000040);exe.write_bytes(b)
            out=root/'profiles'
            self.command('profile.py',exe,'--ring-pointer-rva','0x2008','--output-dir',out)
            digest=hashlib.sha256(b).hexdigest();profile=out/(digest+'.cache')
            self.assertEqual(profile.read_text(),f'aoe4-cache-v1 {digest} 2008 1000000 20\n')
            self.command('profile.py',exe,'--ring-pointer-rva','0x2008','--output-dir',out,ok=False)
            self.command('profile.py',exe,'--ring-pointer-rva','0x1000','--output-dir',out,ok=False)
            self.command('profile.py',exe,'--ring-pointer-rva','0x2001','--output-dir',out,ok=False)
    def test_manifest_pins_actual_archives_and_keeps_renderer_licence_gate(self):
        with tempfile.TemporaryDirectory() as root:
            root=pathlib.Path(root);wine=root/'wine.tar.gz';helper=root/'helper.tar.gz';output=root/'engine.json'
            for path,names in ((wine,['engine/bin/wine','engine/lib/wine/x86_64-unix/ntdll.so','engine/lib/wine/x86_64-windows/ntdll.dll']),
                               (helper,['aoe4/x87sidecar','aoe4/inputs.lock.json'])):
                with tarfile.open(path,'w:gz') as archive:
                    for name in names:
                        info=tarfile.TarInfo(name);info.size=3;archive.addfile(info,io.BytesIO(b'abc'))
            args=['--wine',wine,'--helper',helper,'--output',output,'--release-url','https://github.com/himbeles/highball-engine-aoe4/releases/download/trial-1']
            self.command('make-manifest.py',*args)
            m=json.loads(output.read_text())
            for key,path in (('wine',wine),('aoe4-helper',helper)):
                self.assertEqual(m['components'][key]['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(m['components'][key]['size'],path.stat().st_size)
            self.assertEqual(m['id'],'x64-crossover26.3-aoe4-r1')
            self.assertIn("apple-gptk-license-2023-08-17",m["licenses"])
            self.command('make-manifest.py',*args[:-1],'https://example.com/trial',ok=False)
            with tarfile.open(helper,'w:gz'):pass
            self.command('make-manifest.py',*args,ok=False)
if __name__=='__main__':unittest.main()
