import socketserver
import sys
import json
import common
import _thread

class MergeSocketHandler(socketserver.BaseRequestHandler):
    tracepoint_merge_handler = common.TracepointMerge() 
    def handle(self):
        # self.request is the TCP socket connected to the client
        data = self.request.recv(2048).strip()
        #print("{} wrote:"+format(self.client_address[0]))
        #print(str(self.data))
        # just send back the same data, but upper-cased
        # self.request.sendall(self.data.upper())
        
        try:
            request = json.loads(data.decode('utf-8'))
        except:
            print( data )
            return
        if( request['op_type']=='record_update' ):
            self.tracepoint_merge_handler.record_bucket_update( request['data'] )
        elif( request['op_type']=='tracepoint_request' ):
            self.tracepoint_merge_handler.get_tracepoint_dict()

class MergeSocket:
    def __init__(self):
#        HOST = socket.gethostname()   # Symbolic name, meaning all available interfaces
        HOST = "localhost"   # Symbolic name, meaning all available interfaces
        PORT = 8888 # Arbitrary non-privileged port
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        self.server = socketserver.ThreadingTCPServer((HOST, PORT), MergeSocketHandler)
        self.server.serve_forever()
    def __del__(self):
        try:
            self.server.shutdown()
        except:
            pass

if __name__ == "__main__":
    s = MergeSocket()
