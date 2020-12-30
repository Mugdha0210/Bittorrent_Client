Computer Networks Project - Bittorrent Client 

---------------------------------------------------------------------------------------------------


Package requirements :


Python3.7.6
bencode.py==4.0.0
certifi==2020.6.20
chardet==3.0.4
idna==2.10
requests==2.24.0
speedtest-cli==2.1.2
urllib3==1.25.11


To run the code :


In virtual environment :
$ pip install requirements.txt


Usage : In same directory as code with virtual environment activated
$python3 bittorrent_client.py <filename.torrent> <download location> <max number_of_peers (default = 50)>


Program will stop running once the download is complete unless some fatal error is encountered.


Implemented :
1. Getting list of trackers.
2. Handles trackers running HTTP, HTTPS, UDP protocols.
3. Getting list of peers in compact and non-compact form.
4. Getting list of pieces.
5. Request for rarest piece first during download.
6. Connection status with each peer and download progress displayed on screen.
7. Download of single-file torrents.
8. Download of multi-file torrents.
9. Settings - 
   1. Maximum number of peers to connect to; default 50.
   2. User-specified download destination.
