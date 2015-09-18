import re
import socket
import sys
import urllib2

from urlparse import urlparse

HOST = 'irc.rizon.net'
PORT = 6667
NICK = 'yt_bot'
CHANNEL = '#yt_bot_test'
PREFIX = '\x034YouTube:\x03 '

title_regexp = re.compile('<title>(.+)</title>')

def handle_privmsg(sock, line):
  col_split = line.split(':', 2)
  channel = line.split(' ')[2]
  urls = re.findall('https?://[^\s]+', col_split[2])
  if len(urls) > 0:
    url = urlparse(urls[0])
    if url.netloc.endswith('youtube.com'):
      try:
        page = urllib2.urlopen(urls[0]).read()
        title = title_regexp.search(page).group(1)
        dash = title.rfind(' - ')
        title = title[:dash]
        sock.sendall('PRIVMSG ' + channel + ' :' + PREFIX + title + '\r\n')
        print 'Video ' + urls[0] + ' has title ' + title
      except urllib2.HTTPError:
        print urls[0] + ' not found'

handlers = {
  '001': lambda sock, line: sock.sendall('JOIN ' + CHANNEL + '\r\n'),
  'PING': lambda sock, line: sock.sendall(line.replace('PING', 'PONG')),
  'PRIVMSG': handle_privmsg
}

class YtBot:

  def __init__(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def connect(self, host, port):
    self.sock.connect((host, port))
    self.fd = self.sock.makefile()
    self.sock.sendall('NICK ' + NICK + '\r\n')
    self.sock.sendall('USER bot * * :youtube link bot\r\n')

  def loop(self):
    for line in self.fd:
      space_split = line.split(' ')
      if len(space_split) > 1:
        command = space_split[1].upper()
        if not command in handlers:
          command = space_split[0].upper()
        if command in handlers:
          handlers[command](self.sock, line)

bot = YtBot()
bot.connect(HOST, PORT)
bot.loop()

