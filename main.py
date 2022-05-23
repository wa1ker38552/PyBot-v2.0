import time
import discord
import requests
import os, sys, io
from replit import db
from alive import keepAlive
from threading import Thread
from bs4 import BeautifulSoup
from discord.errors import HTTPException

client = discord.Client()
local_save = {}

def run_script(script):
  old_stdout = sys.stdout
  sys.stdout = buffer = io.StringIO()

  with open('script.py', 'w') as file:
    file.write(script)
  try:
    #Thread(target=lambda: exec(open('script.py', 'r').read())).start(). # Uses threading to catch while loops
    exec(open('script.py', 'r').read())
    
    sys.stdout = old_stdout
    prevPrint = buffer.getvalue()
    return (f'```{prevPrint}```')
  except Exception as error:
    return (f'```diff\n-{error}```')

def find_index(s, i, t):
  start = t.index(s)+len(s)
  x = start
  while t[x] != i: x += 1
  return t[start:x]

def query_package(query):
  response = requests.get(f'https://pypi.org/search/?q={query}')
  
  soup = BeautifulSoup(response.text, 'html.parser')
  unparsed_results = soup.find_all("a", attrs = {"class":"package-snippet"})
  results = {}
  for item in unparsed_results:
    name = find_index('<span class="package-snippet__name">', '<', str(item).split('\n')[2])
    desc = find_index('<p class="package-snippet__description">', '<', str(item).split('\n')[8])
    link = find_index('<a class="package-snippet" href="', '"', str(item).split('\n')[0])
    results[name] = [f'pypi.org{link}', desc]
  return results

def query_codegrepper(query):
  q = query.split()
  q.append('python')
  q = '%20'.join(q)
  request = requests.get(f'https://www.codegrepper.com/api/search.php?q={q}&search_options=search_titles,search_code')
  request = request.json()['answers']
  answers = []
  for item in request:

    answers.append(item['answer'])
  return answers

@client.event
async def on_ready():
  await client.change_presence(activity=discord.Game(name="pycharm"))
  print(client.user)

@client.event
async def on_message(message):
  if client.user != message.author:
    content = str(message.content)
    author = str(message.author)

    if content.split('\n')[0] == '```py':
      script = content.replace('```py', '').replace('```', '')
      local_save[author] = script
      try:
        await message.channel.send(run_script(script))
      except HTTPException: 
        await message.channel.send('```Returned content exceeds Discord 4000 character limit```')
    if content.split()[0] == 'py':
      if content.split()[1] == 'save':
        if author in local_save:
          try:
            if author in db:
              db[author][content.split()[2]] = local_save[author]
            else:
              db[author] = {content.split()[2]: local_save[author]}
            await message.channel.send(f'```Succesfully saved: {content.split()[2]}```')
          except IndexError:
            await message.channel.send('```Missing arguments, (project name)```')
        else:
          await message.channel.send(f'```No recent scripts saved under user: {author}```')
      if content.split()[1] == 'localsave':
        if author in local_save:
          await message.channel.send(f'```py{local_save[author]}```')
        else:
          await message.channel.send(f'```No recent scripts saved under user: {author}```')
      if content.split()[1] == 'scripts':
        if author in db:
          results = []
          for i, item in enumerate(db[author]):
            results.append(f'{i+1}. {item} || {len(db[author][item])/1000} kb')
          await message.channel.send('```'+'\n'.join(results)+'```')
        else:
          await message.channel.send(f'```No saved scripts under user: {author}. Use py save (savename) to save scripts.')    
      if content.split()[1] == 'runscript':
        try:
          if author in db:
            if content.split()[2] in db[author]:
              try:
                await message.channel.send(run_script(db[author][content.split()[2]]))
              except HTTPException: 
                await message.channel.send('```Returned content exceeds Discord 4000 character limit```')
            else:
              await message.channel.send(f'```No script {content.split()[2]} saved onto user {author}.```')
          else:
            await message.channel.send(f'```No saved scripts under user: {author}. Use py save (savename) to save scripts.')      
        except IndexError:
          await message.channel.send('```Missing arguments, (project name)```')
      if content.split()[1] == 'viewscript':
        try:
          if author in db:
            if content.split()[2] in db[author]:
              await message.channel.send(f'```py{db[author][content.split()[2]]}```')
            else:
              await message.channel.send(f'```No script {content.split()[2]} saved onto user {author}.```')
          else:
            await message.channel.send(f'```No saved scripts under user: {author}. Use py save (savename) to save scripts.')      
        except IndexError:
          await message.channel.send('```Missing arguments, (project name)```')
      if content.split()[1] == 'package':
        try:
          results = query_package(content.split()[2])
          format = []
          for key in results:
            format.append(f'{key}: {results[key][0]} || {results[key][1]}')
          if len(str(format)) > 2000:
            await message.channel.send('```'+'\n'.join(format[:int(len(format)/2)])+'```')
            await message.channel.send('```'+'\n'.join(format[int(len(format)/2):])+'```')
          else:
            await message.channel.send('```'+'\n'.join(format)+'```')
        except IndexError:
          await message.channel.send('```Missing arguments, (package name)```')
      if content.split()[1] == 'snippet':
        answers = query_codegrepper(' '.join(content.split()[2:]))
        for answer in answers:
          await message.channel.send(f'```py\n{answer}```')
      if content.split()[1] == 'help':
        embed = discord.Embed()
        embed.color = 0x458cff
        embed.title = 'PyBot Help'
        embed.description  = '''
        To use the bot, write script that start's in code blocks, (**```**py at the front and same thing without py at the back). py is used to highlight syntax in python colors.\n
        Most imports work but may take some time. Imports like selenium, turtle, and tkinter obviously won't work. Scripts that use time, threading, and loops also won't work since the scripts are run on a server. Script names cannot contain spaces. Scripts backup after running.\n
        1. `py save (scriptname)`: Saves your backed-up script to your user
        2. `py localsave`: Checks if your script is backed-up/show current backed-up script
        3. `py scripts`: Shows scrips saved onto your user
        4. `py runscript (scriptname)`: Runs a saved script
        5. `py viewscript (scriptname)`: View a saved script
        6. `py package (packagename)`: Queries list of modules from PyPI
        7. `py snippet (code help)`: Finds code snipper about (x) from codegrepper
        8. `py help`: Show help messages
        '''
        await message.channel.send(embed=embed)
        
keepAlive()
client.run(os.environ['BOT'])
