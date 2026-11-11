/** Контракт реального импорта. null означает отсутствие значения, а не ноль. */
export interface SourceCell {sheet:string; cell:string; value:unknown; formula:boolean}
export interface RecordDefect {
  id:string; sourceId:string; kind:'single'|'group'|'dent'; pipeNumber:string;
  positionM:number|null; lengthMm:number|null; widthMm:number|null; depthMm:number|null; side:string|null;
  source:{sheet:string;row:number;fields:Record<string,SourceCell>};
  inputSources?:Record<string,SourceCell>; inputs?:Record<string,number>;
  raw:Record<string,unknown>; members?:RecordDefect[];
  result:{status:string;pressureMpa:number|null;category:'A'|'B'|'C'|null;
    messages:string[];method?:string;model?:string;steps?:Record<string,unknown>;preliminaryCategory?:'A'|'B'|'C'};
}
export interface Project {
  id:string;name:string;sha256:string;assumptions:string[];defects:RecordDefect[];
  errors:{row:number;id:string;message:string}[];
  summary:{anomRows:number;weldRows:number;defects:number;statuses:Record<string,number>};
}
