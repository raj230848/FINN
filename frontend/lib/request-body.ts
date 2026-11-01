export class BodyReadError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status=status; }
}
export async function readSmallJson(request: Request, limit=2048): Promise<Record<string,unknown>> {
  const declared=Number(request.headers.get("content-length")||0);
  if(declared>limit)throw new BodyReadError("Sign-in request is too large.",413);
  if(!request.body)throw new BodyReadError("A JSON request body is required.",400);
  const reader=request.body.getReader();const parts:Uint8Array[]=[];let size=0;
  for(;;){
    const {done,value}=await reader.read();if(done)break;
    size+=value.byteLength;
    if(size>limit){await reader.cancel();throw new BodyReadError("Sign-in request is too large.",413);}
    parts.push(value);
  }
  const bytes=new Uint8Array(size);let offset=0;
  for(const part of parts){bytes.set(part,offset);offset+=part.byteLength;}
  try {
    const result=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
    if(!result || typeof result!=="object" || Array.isArray(result))throw new Error("Not an object");
    return result;
  } catch { throw new BodyReadError("Provide a valid JSON object.",400); }
}
