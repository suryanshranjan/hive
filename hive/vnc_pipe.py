"""One private inetd VNC connection over Docker exec stdin/stdout. No TCP listener."""
import os
import socket
import subprocess
import threading


def main():
    local, remote = socket.socketpair()
    with local, remote:
        proc = subprocess.Popen(['x11vnc','-inetd','-display',os.environ['DISPLAY'],'-nopw',
                                 '-noclipboard','-nosel','-quiet','-noxdamage'],
                                stdin=remote,stdout=remote,stderr=subprocess.DEVNULL)
        remote.close()
        def input_stream():
            try:
                while data := os.read(0,65536):
                    local.sendall(data)
            finally:
                local.shutdown(socket.SHUT_WR)
        threading.Thread(target=input_stream,daemon=True).start()
        try:
            with os.fdopen(os.dup(1),'wb') as out:
                while data := local.recv(65536):
                    out.write(data)
                    out.flush()
        finally:
            proc.terminate()
            proc.wait(timeout=5)


if __name__ == '__main__':
    main()
