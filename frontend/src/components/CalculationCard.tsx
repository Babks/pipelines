import {Alert,Button,Descriptions,Drawer,Table,Tabs,Tag,Input} from 'antd';
import {useState} from 'react';
import type {RecordDefect} from '../types/project';
const show=(v:unknown):string=>v==null?'Нет данных':typeof v==='object'?JSON.stringify(v):String(v);
export function CalculationCard({defect,onClose,onRecalculate,busy,onRm3}:{defect:RecordDefect|null;onClose:()=>void;onRecalculate:()=>void;busy:boolean;onRm3?:(evidence:string)=>void}) {
  const [evidence,setEvidence]=useState('');
  if(!defect)return null;
  const fields=Object.entries(defect.source.fields).map(([key,s])=>({key,field:key,address:`${s.sheet}!${s.cell}`,value:show(s.value)}));
  const r=defect.result;
  const data=<><Descriptions bordered column={1} size="small" items={[
    {key:'id',label:'Исходный ID',children:defect.sourceId},{key:'row',label:'Источник',children:`anom, строка ${defect.source.row}`},
    {key:'pipe',label:'Труба',children:defect.pipeNumber}]}/><h3>Исходные ячейки</h3>
    <Table size="small" rowKey="key" pagination={{pageSize:12}} dataSource={fields} columns={[
      {title:'Поле',dataIndex:'field'},{title:'Ячейка',dataIndex:'address'},{title:'Значение',dataIndex:'value'}]}/></>;
  const calc=<><p>{r.method??'Метод определяется по исходным данным и условиям применимости.'}</p>
    {defect.kind==='dent'&&onRm3&&<section><Alert type="info" title="Расчёт малой вмятины РМ3" description="Для применения модели нужно документальное подтверждение отсутствия вторичных повреждений. Для остальных вмятин необходимы разделы 2.7 методики РМ1/РМ2."/><Input.TextArea value={evidence} onChange={e=>setEvidence(e.target.value)} placeholder="Документ, пункт и основание отсутствия вторичных повреждений"/><Button loading={busy} disabled={evidence.trim().length<10} onClick={()=>onRm3(evidence)}>Рассчитать РМ3 с указанным основанием</Button></section>}
    <h3>Входы расчёта</h3><Descriptions bordered column={1} size="small" items={Object.entries(defect.inputs??{}).map(([key,v])=>({key,label:key,children:show(v)}))}/>
    <h3>Промежуточные результаты</h3><Descriptions bordered column={1} size="small" items={Object.entries(r.steps??{}).map(([key,v])=>({key,label:key,children:show(v)}))}/>
    <h3>Выбранные источники параметров трубы</h3><Descriptions column={1} items={Object.entries(defect.inputSources??{}).map(([key,s])=>({key,label:key,children:s?`${s.sheet}!${s.cell}: ${show(s.value)}`:'Нет данных'}))}/></>;
  const result=<><Alert type={r.status==='invalid'?'error':'warning'} showIcon title={r.status==='awaiting_rm2'?'Ожидает дополнительного расчёта РМ2':r.status==='provisional'?'Предварительный расчёт по указанным допущениям':'Расчёт требует исходных данных'} description={r.messages.join(' ')}/>
    {r.preliminaryCategory&&<p>Предварительная оценка РМ3: {r.preliminaryCategory}. {r.status==='awaiting_rm2'?'Окончательная категория отсутствует.':''}</p>}
    <Descriptions bordered column={1} items={[{key:'p',label:'Разрушающее давление, МПа',children:r.pressureMpa?.toFixed(6)??'Не определено'},
      {key:'cat',label:'Предварительная категория',children:r.category?<Tag color="orange">{r.category}</Tag>:'Не определена'}]}/></>;
  return <Drawer open size={760} title={`Дефект ${defect.sourceId}`} onClose={onClose} mask={false}
    footer={<Button onClick={onRecalculate} loading={busy}>Пересчитать проект</Button>}>
    <Tabs items={[{key:'data',label:'Данные',children:data},{key:'calc',label:'Расчёт',children:calc},{key:'result',label:'Результат',children:result},...(defect.members?[{key:'members',label:'Состав группы',children:<Table rowKey="id" dataSource={defect.members} pagination={false} columns={[{title:'ID',dataIndex:'sourceId'},{title:'Длина, мм',dataIndex:'lengthMm'},{title:'Глубина, мм',dataIndex:'depthMm'},{title:'Положение, м',dataIndex:'positionM'}]}/>}]:[])]}/>
  </Drawer>;
}
