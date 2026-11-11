import {Alert, Button, Descriptions, Upload} from 'antd';
import {InboxOutlined} from '@ant-design/icons';
import {useState} from 'react';
import {request} from '../api';
import type {Project} from '../types/project';

export function ImportWorkbook({onImported}:{onImported:(p:Project)=>void}) {
  const [file,setFile]=useState<File|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  async function run() {
    if(!file) return;
    setBusy(true);setError('');
    try {const data=new FormData();data.append('file',file);onImported(await request<Project>('/import',{method:'POST',body:data}));}
    catch(e){setError(String(e instanceof Error?e.message:e));}finally{setBusy(false);}
  }
  return <section className="surface upload-main">
    <h1>Загрузка данных ВТД</h1>
    <p>Книга сохраняется и обрабатывается на этом компьютере. Ожидаются листы anom и weld.</p>
    <Upload.Dragger accept=".xlsx" multiple={false} showUploadList={false} disabled={busy} beforeUpload={f=>{
      if(!f.name.toLowerCase().endsWith('.xlsx')||f.size===0||f.size>50*1024*1024){setError('Выберите непустой .xlsx до 50 МБ');return false;}
      setError('');setFile(f);return false;
    }}><InboxOutlined style={{fontSize:40,color:'#1677ff'}}/><h3>Выберите или перетащите Excel</h3><p>{file?.name??'.xlsx · до 50 МБ'}</p></Upload.Dragger>
    <Descriptions column={1} items={[{key:'s',label:'Листы',children:'anom — аномалии; weld — параметры труб'},
      {key:'p',label:'Профиль расчёта',children:'Совместимость со старым скриптом: pd; десятичные часы; одометр в метрах'},
      {key:'v',label:'Проверка',children:busy?'Чтение книги и проверка строк…':'Проверка начнётся после нажатия кнопки'}]}/>
    <Alert type="warning" showIcon title="Условия интерпретации исходных данных" description="Справочники оставляют смысл pd и единицы углов неподтверждёнными. Вычисления по профилю старого скрипта будут отмечены как предварительные; исходные значения и адреса ячеек сохраняются."/>
    {error&&<Alert style={{marginTop:16}} type="error" showIcon title="Ошибка импорта" description={error}/>}
    <Button style={{marginTop:24}} type="primary" loading={busy} disabled={!file} onClick={run}>Проверить и импортировать</Button>
  </section>;
}
