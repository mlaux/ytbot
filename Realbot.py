import re
import socket
import sys
import urllib2

from urlparse import urlparse
from RealbotStorage import RealbotStorage

HOST = 'irc.rizon.net'
PORT = 6667
NICK = 'real'
CHANNEL = '#ethereal'
PREFIX = '\x034YouTube:\x03 '
DB_FILE = 'realbot.db'

title_regexp = re.compile(r'<title>(.+)</title>')
karma_regexp = re.compile(r'(\w+)(\+\+|--)')
storage = RealbotStorage(DB_FILE)

def send(sock, channel, message):
  sock.sendall('PRIVMSG ' + channel + ' :' + message + '\r\n')

def handle_youtube(sock, url, channel):
  try:
    page = urllib2.urlopen(url).read()
    title = title_regexp.search(page).group(1)
    dash = title.rfind(' - ')
    title = title[:dash]
    send(sock, channel, PREFIX + title)
    print 'Video ' + url + ' has title ' + title
  except urllib2.HTTPError:
    print url + ' not found'

def handle_karma(sock, sender, channel, entity, increment):
  if sender.lower() == entity.lower():
    if increment:
      send(sock, channel, 'No cheating!')
    else:
      send(sock, channel, 'Don\'t be so hard on yourself!')
    return

  row = storage.query('SELECT karma FROM karma WHERE entity = ?', 
                       (entity,), True)
  needs_insert = False

  if row is None:
    cur_val = 0
    needs_insert = True
  else:
    cur_val = row['karma']
  cur_val = cur_val + 1 if increment else cur_val - 1

  if needs_insert:
    storage.query('INSERT INTO karma(entity, karma) VALUES (?, ?)',
                  (entity, cur_val))
  else:
    storage.query('UPDATE karma SET karma = ? WHERE entity = ?',
                  (cur_val, entity))
  
  message = entity + '\'s karma has ' + ('increased' if increment else 'decreased') + ' to ' + str(cur_val) + '!'
  send(sock, channel, message)

def handle_privmsg(sock, line):
  col_split = line.split(':', 2)
  sender = line[1:line.index('!')]
  channel = line.split(' ')[2]
  urls = re.findall('https?://[^\s]+', col_split[2])
  plusplus = karma_regexp.finditer(col_split[2])
  if len(urls) > 0:
    url = urlparse(urls[0])
    if url.netloc.endswith('youtube.com'):
      handle_youtube(sock, urls[0], channel)
  for karma_expr in plusplus:
    handle_karma(sock, sender, channel, karma_expr.group(1), 
                 True if karma_expr.group(2) == '++' else False)

handlers = {
  '001': lambda sock, line: sock.sendall('JOIN ' + CHANNEL + '\r\n'),
  'PING': lambda sock, line: sock.sendall(line.replace('PING', 'PONG')),
  'PRIVMSG': handle_privmsg
}

class Realbot:

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

if __name__ == "__main__":
  bot = Realbot()
  bot.connect(HOST, PORT)
  bot.loop()

