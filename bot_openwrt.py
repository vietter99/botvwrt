#!/usr/bin/env python3
_W='output'
_V='Lỗi gọi Gemini API.'
_U='message'
_T='application/json'
_S='Content-Type'
_R='chat_id'
_Q='gemini'
_P='user'
_O='system'
_N='openai'
_M='read'
_L='\n\n'
_K=True
_J='gemini_key'
_I='openai_key'
_H='commands'
_G='mode'
_F='text'
_E='admin_id'
_D='telegram_token'
_C='role'
_B='content'
_A=None
import time,json,os,requests,subprocess,shlex
from requests.exceptions import ReadTimeout,ConnectionError
TELEGRAM_TOKEN=os.getenv('TELEGRAM_TOKEN','')
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY','')
OPENAI_API_KEY=os.getenv('OPENAI_API_KEY','')
ADMIN_ID_STR=os.getenv('ADMIN_ID','0')
try:ADMIN_ID=int(ADMIN_ID_STR)
except ValueError:ADMIN_ID=0
GEMINI_MODEL_NAME='gemini-2.5-flash'
OPENAI_MODEL_NAME='gpt-4.1-mini'
TELEGRAM_API=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
GEMINI_URL=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
OPENAI_URL='https://api.openai.com/v1/chat/completions'
DEFAULT_LLM_MODE=_N
current_llm_mode=DEFAULT_LLM_MODE
ADMIN_IDS={ADMIN_ID}
HELP_TEXT='\nChào Sếp, em là VWRT bot 👋. Cách dùng nhanh:\n1) Chat bình thường\n   - Cứ nhắn câu hỏi bất kỳ (IT, mạng, đời sống...), em trả lời bằng AI.\n   - Mặc định đang dùng ChatGPT (OpenAI).\n2) Đổi giữa ChatGPT và Gemini\n   - /use_chatgpt  → dùng ChatGPT (OpenAI)\n   - /use_gemini   → dùng Gemini\n3) Điều khiển router OpenWrt qua Telegram\n   - Dùng /rt rồi nói tiếng Việt bình thường:\n   Ví dụ:\n   - /rt cho mình xem client đang kết nối Wi-Fi\n   - /rt đổi mật khẩu wifi 5G thành 12345678\n   - /rt xem thông tin router\n   - /rt reboot router (tùy em hiểu, sẽ do AI quyết định lệnh)\nGợi ý:\n- Gõ /use_gemini hoặc /use_chatgpt trước, rồi chat thử vài câu.\n'
def send_message(chat_id,text,reply_to_message_id=_A):
	B=reply_to_message_id;C={_R:chat_id,_F:text}
	if B is not _A:C['reply_to_message_id']=B
	try:
		A=requests.post(f"{TELEGRAM_API}/sendMessage",data=C,timeout=10)
		if not A.ok:print('send_message failed:',A.status_code,A.text)
	except Exception as D:print('send_message error:',D)
def call_openai_messages(messages):
	B={'Authorization':f"Bearer {OPENAI_API_KEY}",_S:_T};C={'model':OPENAI_MODEL_NAME,'messages':messages}
	try:A=requests.post(OPENAI_URL,headers=B,data=json.dumps(C),timeout=20);A.raise_for_status();D=A.json();return D['choices'][0][_U][_B].strip()
	except Exception as E:print('call_openai_messages error:',E);return
def call_openai(prompt):A=call_openai_messages([{_C:_O,_B:'You are a helpful assistant.'},{_C:_P,_B:prompt}]);return A or'Lỗi gọi OpenAI API.'
def call_gemini(prompt):
	E='Gemini không trả về nội dung.';D='parts';F={_S:_T};G={'contents':[{D:[{_F:prompt}]}]}
	try:
		A=requests.post(GEMINI_URL,headers=F,data=json.dumps(G),timeout=20);A.raise_for_status();H=A.json();B=H.get('candidates',[])
		if not B:return E
		C=B[0].get(_B,{}).get(D,[])
		if not C:return E
		return C[0].get(_F,'').strip()
	except Exception as I:print('call_gemini error:',I);return _V
def run_openwrt_cmd(cmd):
	'\n    Chạy lệnh shell trực tiếp trên OpenWrt (vì bot đang chạy ngay trên router).\n    '
	try:
		A=subprocess.run(cmd,shell=_K,capture_output=_K,text=_K,timeout=20);B=A.stdout.strip();D=A.stderr.strip()
		if A.returncode!=0:return f"Command failed (code {A.returncode}):\n{D or B}"
		return B or'(Không có output)'
	except Exception as C:print('run_openwrt_cmd error:',C);return f"Lỗi khi chạy lệnh: {C}"
def parse_router_shell_llm(text,router_env_text):
	'\n    Dùng LLM (OpenAI hoặc Gemini tùy current_llm_mode) để chuyển\n    câu tự nhiên -> JSON chứa lệnh shell OpenWrt.\n    ';D='\nBạn là bộ sinh lệnh shell cho router OpenWrt.\n\nNhiệm vụ:\n- Nhận mô tả bằng tiếng Việt hoặc tiếng Anh về việc cần làm trên router.\n- Dựa trên THÔNG TIN MÔI TRƯỜNG ĐƯỢC CUNG CẤP (iw dev, ip link show, ubus list, uci show wireless, ...) để sinh ra DANH SÁCH LỆNH SHELL cần chạy.\n- CHỈ TRẢ VỀ JSON HỢP LỆ, KHÔNG THÊM BẤT KỲ CHỮ NÀO KHÁC.\n\nĐịnh dạng JSON BẮT BUỘC:\n\n{\n  "mode": "read" | "write",\n  "commands": [ "cmd1", "cmd2", "cmd3" ]\n}\n\nGiải thích:\n- "mode":\n  - "read": chỉ xem thông tin, không thay đổi cấu hình.\n  - "write": có thay đổi cấu hình hoặc trạng thái.\n- "commands": danh sách lệnh shell sẽ chạy lần lượt bằng quyền root.\n\nQUY TẮC:\n- Chọn interface, section uci, ubus object... DỰA TRÊN router_env_text, không được bịa.\n- Được quyền thay đổi cấu hình, nhưng TRÁNH các lệnh phá hoại toàn bộ hệ thống như:\n  rm -rf /, mkfs.*, dd ghi đè toàn bộ đĩa, format phân vùng, ...\n- Nếu yêu cầu mơ hồ hoặc quá nguy hiểm, hãy ưu tiên sinh các lệnh chỉ-đọc (mode="read").\n- Chỉ khi hoàn toàn không suy ra được bất kỳ lệnh an toàn nào thì mới trả về:\n  {\n    "mode": "read",\n    "commands": []\n  }\n\nYÊU CẦU TUYỆT ĐỐI:\n- Không giải thích.\n- Không comment.\n- Không thêm text ngoài JSON.\n- JSON phải đúng cú pháp chuẩn.\n';E=f'''
Yêu cầu của admin:

"""{text}"""

Dưới đây là thông tin môi trường thực tế của router:

"""{router_env_text}"""

Hãy trả về JSON đúng định dạng đã mô tả ở trên.
''';global current_llm_mode;B=_A
	if current_llm_mode==_Q:
		B=call_gemini(D+_L+E)
		if not B or B.startswith(_V)or'Gemini không trả về nội dung'in B:print('parse_router_shell_llm: Gemini fail, thử OpenAI fallback');B=call_openai_messages([{_C:_O,_B:D},{_C:_P,_B:E}])
	else:
		B=call_openai_messages([{_C:_O,_B:D},{_C:_P,_B:E}])
		if not B:print('parse_router_shell_llm: OpenAI fail, thử Gemini fallback');B=call_gemini(D+_L+E)
	if not B:print('DEBUG parse_router_shell_llm: LLM trả về rỗng sau khi đã fallback');return{_G:_M,_H:[]}
	print('DEBUG parse_router_shell_llm RAW:',B)
	try:
		A=B.strip()
		if A.startswith('```'):
			A=A.strip('`')
			if A.lower().startswith('json'):A=A[4:].lstrip()
		if'{'in A and'}'in A:G=A.find('{');H=A.rfind('}');A=A[G:H+1]
		F=json.loads(A);I=F.get(_G,_M);C=F.get(_H,[])
		if not isinstance(C,list):C=[]
		C=[A for A in C if isinstance(A,str)and A.strip()];return{_G:I,_H:C}
	except Exception as J:print('parse_router_shell_llm JSON error:',J);return{_G:_M,_H:[]}
def collect_router_env():
	'\n    Thu thập một số thông tin cơ bản trên router để LLM không đoán mò.\n    Không cần chỉnh theo từng lệnh, chỉ là bộ khảo sát chung.\n    ';C={'iw_dev':'iw dev','ip_link':'ip link show','ubus_list':'ubus list','uci_wireless':'uci show wireless'};A={}
	for(D,B)in C.items():E=run_openwrt_cmd(B);A[D]={'cmd':B,_W:E}
	return A
def format_env_for_llm(env_outputs):
	'\n    Chuyển env_outputs thành một chuỗi text nhét vào prompt cho LLM.\n    ';A=[]
	for(C,B)in env_outputs.items():D=B['cmd'];E=B[_W];A.append(f"### {C}\n# Command: {D}\n{E}\n")
	return'\n'.join(A)
def extract_clients_from_outputs(cmd_outputs):
	"\n    cmd_outputs: list[(cmd, out)]\n    Trích client từ các output của lệnh 'ip neigh ...'\n\n    Logic:\n    - Gom theo MAC: mỗi MAC = 1 client.\n    - Ưu tiên IPv4, nếu không có IPv4 thì lấy IPv6.\n    - Chỉ lấy các interface LAN/Wi-Fi nội bộ: br-*, lan*, wl*, ra*.\n    ";N='lladdr';M='dev';H='iface';G='ipv6';F='ipv4';K={}
	for(O,P)in cmd_outputs:
		if'ip neigh'not in O:continue
		for B in P.splitlines():
			B=B.strip()
			if not B or M not in B or N not in B:continue
			D=B.split()
			try:C=D[0];Q=D.index(M);A=D[Q+1];R=D.index(N);I=D[R+1]
			except(ValueError,IndexError):continue
			if not(A.startswith('br-')or A.startswith('lan')or A.startswith('wl')or A.startswith('ra')):continue
			E=K.setdefault(I,{F:_A,G:_A,H:A})
			if':'in C:
				if E[G]is _A:E[G]=C
			elif E[F]is _A:E[F]=C
			E[H]=A
	L=[]
	for(I,J)in K.items():
		C=J[F]or J[G];A=J[H]
		if C is _A:continue
		L.append({'ip':C,'mac':I,H:A})
	return L
def handle_router_nlu(from_id,natural_text):
	D=natural_text
	if from_id not in ADMIN_IDS:return'Bạn không có quyền điều khiển router.'
	K=collect_router_env();L=format_env_for_llm(K);E=parse_router_shell_llm(D,L);M=E.get(_G,_M);F=E.get(_H,[])
	if not F:return'LLM không sinh được lệnh nào cho yêu cầu này.'
	N=['rm -rf /','mkfs',':(){:|:&};:','dd if=','mkfs.'];B=[]
	for A in F:
		for G in N:
			if G in A:return f"Lệnh bị chặn vì chứa chuỗi nguy hiểm: {G}\nLệnh: {A}"
		B.append(A)
	H=[]
	for A in B:O=run_openwrt_cmd(A);H.append((A,O))
	I=[f"$ {A}\n{B}"for(A,B)in H];P=_L.join(I);J=f'''
Bạn là trợ lý cho admin đang điều khiển router OpenWrt qua SSH.

Yêu cầu ban đầu của admin:
"""{D}"""

Dưới đây là CÁC LỆNH đã chạy trên router và OUTPUT tương ứng:

"""{P}"""

Hãy trả lời NGẮN GỌN, RÕ RÀNG bằng tiếng Việt cho admin:

- Mô tả ngắn gọn bạn đã làm gì (theo kết quả lệnh).
- Đưa ra kết luận hữu ích: ví dụ client nào đang kết nối, password đã đổi chưa, thông tin hệ thống gì, v.v.
- Nếu thao tác có thay đổi cấu hình (mode="write"), hãy nhắc lại ngắn gọn điều đã thay đổi.
- Không in lại lệnh shell.
- Không dump lại toàn bộ output.
- Tối đa 6–8 dòng.
- Nếu không làm được điều admin yêu cầu (ví dụ lệnh lỗi), hãy nói rõ lý do (theo output) và gợi ý lệnh khác nếu có.
''';global current_llm_mode
	if current_llm_mode==_Q:C=call_gemini(J)
	else:C=call_openai(J)
	if not C:Q=f"[MODE: {M}] Đã chạy {len(B)} lệnh trên router:\n";return Q+_L.join(I)
	return C.strip()
def handle_chat_message(text):
	global current_llm_mode
	if current_llm_mode==_N:return call_openai(text)
	else:return call_gemini(text)
UCI_CONFIG_PATH='/etc/config/telegram_bot'
def mask_value(value,show=4):
	B=show;A=value
	if not A:return'(chưa cấu hình)'
	A=A.strip()
	if len(A)<=B:return'*'*len(A)
	return'*'*(len(A)-B)+A[-B:]
def load_uci_current():
	"\n    Đọc /etc/config/telegram_bot (nếu có) để lấy giá trị hiện tại.\n    Parse đơn giản:\n      option telegram_token 'VALUE'\n    ";D="'";C={_D:'',_I:'',_J:'',_E:'0'}
	if not os.path.exists(UCI_CONFIG_PATH):return C
	try:
		with open(UCI_CONFIG_PATH,'r')as E:
			for B in E:
				B=B.strip()
				if B.startswith('option telegram_token'):
					A=B.split(D,2)
					if len(A)>=2:C[_D]=A[1]
				elif B.startswith('option openai_key'):
					A=B.split(D,2)
					if len(A)>=2:C[_I]=A[1]
				elif B.startswith('option gemini_key'):
					A=B.split(D,2)
					if len(A)>=2:C[_J]=A[1]
				elif B.startswith('option admin_id'):
					A=B.split(D,2)
					if len(A)>=2:C[_E]=A[1]
	except Exception as F:print('load_uci_current error:',F)
	return C
def write_uci_config(cfg):
	'\n    Ghi lại file /etc/config/telegram_bot theo format UCI.\n    ';A=cfg;B=f"""config bot 'main'
    option telegram_token '{A[_D]}'
    option openai_key     '{A[_I]}'
    option gemini_key     '{A[_J]}'
    option admin_id       '{A[_E]}'
"""
	try:
		with open(UCI_CONFIG_PATH,'w')as C:C.write(B)
		os.chmod(UCI_CONFIG_PATH,384);print(f"Đã ghi cấu hình vào {UCI_CONFIG_PATH}")
	except Exception as D:print('write_uci_config error:',D)
def send_hello_after_config(token,admin_id):
	'\n    Sau khi wizard lưu cấu hình lần đầu,\n    dùng token + admin_id mới để gửi lời chào / hướng dẫn.\n    ';C=token;A=admin_id
	if not C:print('send_hello_after_config: TELEGRAM_TOKEN rỗng, bỏ qua.');return
	if not A or A=='0':print('send_hello_after_config: ADMIN_ID rỗng hoặc 0, bỏ qua.');return
	try:D=int(A)
	except ValueError:print(f"send_hello_after_config: ADMIN_ID không phải số: {A!r}");return
	E=f"https://api.telegram.org/bot{C}/sendMessage";F=HELP_TEXT
	try:
		B=requests.post(E,data={_R:D,_F:F},timeout=10)
		if not B.ok:print('send_hello_after_config: sendMessage failed:',B.status_code,B.text)
		else:print(f"send_hello_after_config: Đã gửi lời chào tới {D}.")
	except Exception as G:print('send_hello_after_config error:',G)
def run_config_wizard():
	'\n    Chạy wizard cấu hình UCI:\n      python3 /root/bot_openwrt.py config\n    ';print('=== VWRT Bot config wizard (UCI) ===');print(f"File: {UCI_CONFIG_PATH}");print('Nhấn Enter để giữ nguyên giá trị đang có.\n');A=load_uci_current();print(f"Hiện TELEGRAM_TOKEN: {mask_value(A[_D])}");C=input('Nhập TELEGRAM_TOKEN mới (BotFather) [Enter = giữ nguyên]: ').strip()
	if C:A[_D]=C
	print(f"Hiện OPENAI_API_KEY: {mask_value(A[_I])}");D=input('Nhập OPENAI_API_KEY mới [Enter = giữ nguyên]: ').strip()
	if D:A[_I]=D
	print(f"Hiện GEMINI_API_KEY: {mask_value(A[_J])}");E=input('Nhập GEMINI_API_KEY mới [Enter = giữ nguyên]: ').strip()
	if E:A[_J]=E
	print(f"Hiện ADMIN_ID: {A[_E]}");B=input('Nhập ADMIN_ID mới (Telegram user id) [Enter = giữ nguyên]: ').strip()
	if B:
		if B.isdigit():A[_E]=B
		else:print('ADMIN_ID phải là số, giữ nguyên giá trị cũ.')
	write_uci_config(A);print('\nĐang gửi lời chào tới ADMIN_ID bằng token mới...');send_hello_after_config(A[_D],A[_E]);print('Đang restart service bot VWRT')
	try:os.system('/etc/init.d/telegram_bot restart')
	except Exception as F:print('Lỗi khi restart service:',F);print('Bạn có thể tự chạy: /etc/init.d/telegram_bot restart')
def main():
	global current_llm_mode
	if not TELEGRAM_TOKEN:print('[FATAL] TELEGRAM_TOKEN đang rỗng. Hãy chạy:');print('  python3 /root/bot_openwrt.py config');print('để cấu hình token/API key, rồi restart service.');return
	print('VWRT started...');print(f"ADMIN_ID: {ADMIN_ID}");print(f"Current LLM mode: {current_llm_mode}");D=_A
	while _K:
		try:
			H={'timeout':50}
			if D is not _A:H['offset']=D
			K=requests.get(f"{TELEGRAM_API}/getUpdates",params=H,timeout=60);E=K.json()
			if not E.get('ok'):print('getUpdates not ok:',E);time.sleep(2);continue
			for I in E.get('result',[]):
				D=I['update_id']+1;C=I.get(_U)
				if not C:continue
				F=C['chat']['id'];J=C['from']['id'];A=C.get(_F);L=C.get('message_id')
				if not A:continue
				A=A.strip();print(f"[UPDATE] from {J} in chat {F}: {A}")
				if A.startswith('/start'):B=HELP_TEXT
				elif A.startswith('/use_chatgpt'):current_llm_mode=_N;B='Đã chuyển sang dùng ChatGPT (OpenAI).'
				elif A.startswith('/use_gemini'):current_llm_mode=_Q;B='Đã chuyển sang dùng Gemini.'
				elif A.startswith('/rt '):M=A[4:].strip();B=handle_router_nlu(J,M)
				else:B=handle_chat_message(A)
				if B:print(f"[REPLY] to {F}: {B[:80]!r}");send_message(F,B,reply_to_message_id=L)
		except ReadTimeout:continue
		except ConnectionError as G:print('Telegram connection error:',G);time.sleep(5);continue
		except Exception as G:print('Loop error:',G);time.sleep(3)
if __name__=='__main__':
	import sys
	if len(sys.argv)>1 and sys.argv[1]=='config':run_config_wizard()
	else:main()
