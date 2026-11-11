// Отдельный API с временной базой: E2E никогда не изменяют пользовательские проекты.
import {spawn} from 'node:child_process';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
const data=mkdtempSync(resolve(tmpdir(),'vtd-e2e-'));
const root=resolve('..');
const python=resolve(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
const child=spawn(python,['-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8017'],{cwd:root,stdio:'inherit',env:{...process.env,VTD_DATA_DIR:data,VTD_SESSION_TOKEN:''}});
process.on('SIGTERM',()=>child.kill());
process.on('SIGINT',()=>child.kill());
child.on('exit',code=>{rmSync(data,{recursive:true,force:true});process.exit(code??0);});
