import os, sqlite3, logging, html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

DB = os.getenv('DB_PATH','database.db')
TOKEN = os.getenv('BOT_TOKEN','')
ADMINS = {int(x.strip()) for x in os.getenv('ADMIN_IDS','').split(',') if x.strip().isdigit()}
logging.basicConfig(level=logging.INFO)

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,description TEXT,password TEXT DEFAULT '',enabled INTEGER DEFAULT 1,sort_order INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS resources(id INTEGER PRIMARY KEY AUTOINCREMENT,version_id INTEGER,name TEXT,description TEXT,url TEXT,icon TEXT DEFAULT 'LINK',enabled INTEGER DEFAULT 1,FOREIGN KEY(version_id) REFERENCES versions(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,description TEXT,url TEXT,enabled INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS socials(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,url TEXT,enabled INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS users(telegram_id INTEGER PRIMARY KEY,username TEXT,first_name TEXT,last_seen TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    defaults={'site_name':'AURA FFX','site_description':'Premium Free Fire resources, tools and projects.','logo_url':'https://i.postimg.cc/k5KrRYWW/photo-2026-08-04-21-28-30.jpg','primary_color':'#00e5ff','secondary_color':'#3a86ff','bg_color':'#030b16','main_download':'','youtube':'https://youtube.com/@devyasin','telegram':'','facebook':'https://www.facebook.com/share/1GU9oTTzeo/','tiktok':'https://www.tiktok.com/@devxyasin?_r=1&_t=ZS-98z424ab17p','instagram':'https://www.instagram.com/devxyasin?igsh=MWU3enozaW9zdHAxeQ==','discord':'https://discord.com/invite/HnYMABuAPj'}
    for k,v in defaults.items(): c.execute('INSERT OR IGNORE INTO settings VALUES (?,?)',(k,v))
    if c.execute('SELECT COUNT(*) n FROM versions').fetchone()['n']==0:
        versions=[('Version 1.0','Bot Version 1.0',''),('Version 2.0','Bot Version 2.0',''),('Version 2.5','temp mal website',''),('Version 3.0','Updated resources',''),('Version 3.5','Updated resources',''),('Version 4.0','Updated resources',''),('Version 4.5','Updated resources',''),('Version 5.0','Latest version',''),('Version 5.5','Latest version','')]
        for i,(n,d,p) in enumerate(versions): c.execute('INSERT INTO versions(name,description,password,sort_order) VALUES(?,?,?,?,?)'.replace('VALUES(?,?,?,?,?)','VALUES(?,?,?,?)'),(n,d,p,i))
    if c.execute('SELECT COUNT(*) n FROM projects').fetchone()['n']==0:
        c.executemany('INSERT INTO projects(name,description,url) VALUES(?,?,?)',[('Connect FFX Server','Access and connect to the main server','/urlapp'),('Free Hosting','Get free hosting for your website','ffxh.html')])
    if c.execute('SELECT COUNT(*) n FROM socials').fetchone()['n']==0:
        c.executemany('INSERT INTO socials(name,url) VALUES(?,?)',[('YouTube',defaults['youtube']),('Facebook',defaults['facebook']),('TikTok',defaults['tiktok']),('Instagram',defaults['instagram']),('Discord',defaults['discord'])])
    c.commit(); c.close()

def set_setting(k,v):
    c=db(); c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,v)); c.commit(); c.close()

def get_settings():
    c=db(); rows=c.execute('SELECT key,value FROM settings').fetchall(); c.close(); return {r['key']:r['value'] for r in rows}

def admin(update): return update.effective_user and update.effective_user.id in ADMINS

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if not admin(update): return await update.message.reply_text('Access denied.')
    await update.message.reply_text('AURA Admin Panel\nChoose an option:',reply_markup=menu())

def menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton('Website Settings',callback_data='settings'),InlineKeyboardButton('Versions',callback_data='versions')],
      [InlineKeyboardButton('Resources',callback_data='resources'),InlineKeyboardButton('Projects',callback_data='projects')],
      [InlineKeyboardButton('Social Links',callback_data='socials'),InlineKeyboardButton('Users',callback_data='users')],
      [InlineKeyboardButton('Broadcast',callback_data='broadcast'),InlineKeyboardButton('Refresh',callback_data='home')]
    ])

async def cb(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if q.from_user.id not in ADMINS: return await q.edit_message_text('Access denied.')
    d=q.data
    if d=='home': return await q.edit_message_text('AURA Admin Panel',reply_markup=menu())
    if d=='settings':
        s=get_settings(); text='WEBSITE SETTINGS\n\n' + '\n'.join(f'{k}: {v}' for k,v in s.items())
        kb=[[InlineKeyboardButton('Change Logo URL',callback_data='set:logo_url'),InlineKeyboardButton('Site Name',callback_data='set:site_name')],[InlineKeyboardButton('Primary Color',callback_data='set:primary_color'),InlineKeyboardButton('Secondary Color',callback_data='set:secondary_color')],[InlineKeyboardButton('Background Color',callback_data='set:bg_color'),InlineKeyboardButton('Description',callback_data='set:site_description')],[InlineKeyboardButton('Main Download',callback_data='set:main_download')],[InlineKeyboardButton('Back',callback_data='home')]]
        return await q.edit_message_text(text[:4000],reply_markup=InlineKeyboardMarkup(kb))
    if d.startswith('set:'):
        key=d.split(':',1)[1]; context.user_data['await']=key
        return await q.edit_message_text(f'Send new value for: {key}\n\nBack: /cancel')
    if d=='versions':
        c=db(); rows=c.execute('SELECT * FROM versions ORDER BY sort_order,id').fetchall(); c.close()
        kb=[[InlineKeyboardButton(f"{r['name']} {'ON' if r['enabled'] else 'OFF'}",callback_data=f'vt:{r["id"]}')] for r in rows]
        kb.append([InlineKeyboardButton('Add Version',callback_data='vadd'),InlineKeyboardButton('Back',callback_data='home')])
        return await q.edit_message_text('VERSIONS\nTap a version to edit.',reply_markup=InlineKeyboardMarkup(kb))
    if d=='vadd': context.user_data['flow']='vadd'; return await q.edit_message_text('Send version as:\nNAME | DESCRIPTION | PASSWORD(optional)')
    if d.startswith('vt:'):
        vid=int(d.split(':')[1]); c=db(); r=c.execute('SELECT * FROM versions WHERE id=?',(vid,)).fetchone(); c.close()
        kb=[[InlineKeyboardButton('Toggle',callback_data=f'vtoggle:{vid}'),InlineKeyboardButton('Delete',callback_data=f'vdel:{vid}')],[InlineKeyboardButton('Back',callback_data='versions')]]
        return await q.edit_message_text(f"{r['name']}\n{r['description']}\nPassword: {'Yes' if r['password'] else 'No'}",reply_markup=InlineKeyboardMarkup(kb))
    if d.startswith('vtoggle:'):
        vid=int(d.split(':')[1]); c=db(); c.execute('UPDATE versions SET enabled=1-enabled WHERE id=?',(vid,)); c.commit(); c.close(); return await q.edit_message_text('Updated.',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Back',callback_data='versions')]]))
    if d.startswith('vdel:'):
        vid=int(d.split(':')[1]); c=db(); c.execute('DELETE FROM resources WHERE version_id=?',(vid,)); c.execute('DELETE FROM versions WHERE id=?',(vid,)); c.commit(); c.close(); return await q.edit_message_text('Deleted.',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Back',callback_data='versions')]]))
    if d=='resources':
        c=db(); rows=c.execute('SELECT r.*,v.name vn FROM resources r LEFT JOIN versions v ON v.id=r.version_id ORDER BY r.id DESC LIMIT 30').fetchall(); c.close()
        text='RESOURCES\n\n'+('\n'.join(f"#{r['id']} {r['name']} → {r['vn']}" for r in rows) if rows else 'No resources yet')
        return await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Add Resource',callback_data='radd')],[InlineKeyboardButton('Back',callback_data='home')]]))
    if d=='radd': context.user_data['flow']='radd'; return await q.edit_message_text('Send resource as:\nVERSION_ID | NAME | DESCRIPTION | URL | ICON')
    if d=='projects':
        c=db(); rows=c.execute('SELECT * FROM projects').fetchall(); c.close(); text='PROJECTS\n\n'+('\n'.join(f"#{r['id']} {r['name']} — {r['url']}" for r in rows) if rows else 'None')
        return await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Add Project',callback_data='padd')],[InlineKeyboardButton('Back',callback_data='home')]]))
    if d=='padd': context.user_data['flow']='padd'; return await q.edit_message_text('Send project as:\nNAME | DESCRIPTION | URL')
    if d=='socials':
        c=db(); rows=c.execute('SELECT * FROM socials').fetchall(); c.close(); text='SOCIAL LINKS\n\n'+('\n'.join(f"#{r['id']} {r['name']} — {r['url']}" for r in rows) if rows else 'None')
        return await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Add Social',callback_data='sadd')],[InlineKeyboardButton('Back',callback_data='home')]]))
    if d=='sadd': context.user_data['flow']='sadd'; return await q.edit_message_text('Send social as:\nNAME | URL')
    if d=='users':
        c=db(); n=c.execute('SELECT COUNT(*) n FROM users').fetchone()['n']; c.close(); return await q.edit_message_text(f'Users registered: {n}',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Back',callback_data='home')]]))
    if d=='broadcast': context.user_data['await']='broadcast'; return await q.edit_message_text('Send broadcast message. /cancel to stop.')

async def msg(update:Update,context:ContextTypes.DEFAULT_TYPE):
    u=update.effective_user
    c=db(); c.execute('INSERT INTO users(telegram_id,username,first_name,last_seen) VALUES(?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name,last_seen=CURRENT_TIMESTAMP',(u.id,u.username,u.first_name)); c.commit(); c.close()
    if u.id not in ADMINS: return
    text=update.message.text or ''
    if text=='/cancel': context.user_data.clear(); return await update.message.reply_text('Cancelled.',reply_markup=menu())
    if context.user_data.get('await')=='broadcast':
        c=db(); ids=[r['telegram_id'] for r in c.execute('SELECT telegram_id FROM users').fetchall()]; c.close(); sent=0
        for uid in ids:
            try: await context.bot.send_message(uid,text); sent+=1
            except: pass
        context.user_data.clear(); return await update.message.reply_text(f'Broadcast sent to {sent} users.',reply_markup=menu())
    key=context.user_data.pop('await',None)
    if key:
        set_setting(key,text.strip()); return await update.message.reply_text(f'{key} updated.',reply_markup=menu())
    flow=context.user_data.pop('flow',None)
    if flow:
        try:
            p=[x.strip() for x in text.split('|')]
            c=db()
            if flow=='vadd': c.execute('INSERT INTO versions(name,description,password,sort_order) VALUES(?,?,?,?)',(p[0],p[1],p[2] if len(p)>2 else '',999))
            elif flow=='radd': c.execute('INSERT INTO resources(version_id,name,description,url,icon) VALUES(?,?,?,?,?)',(int(p[0]),p[1],p[2],p[3],p[4] if len(p)>4 else 'LINK'))
            elif flow=='padd': c.execute('INSERT INTO projects(name,description,url) VALUES(?,?,?)',(p[0],p[1],p[2]))
            elif flow=='sadd': c.execute('INSERT INTO socials(name,url) VALUES(?,?)',(p[0],p[1]))
            c.commit(); c.close(); return await update.message.reply_text('Saved.',reply_markup=menu())
        except Exception as e: return await update.message.reply_text('Invalid format. Please try again. '+str(e))

async def cancel(update,context): context.user_data.clear(); await update.message.reply_text('Cancelled.',reply_markup=menu())

if __name__=='__main__':
    init_db()
    if not TOKEN: raise SystemExit('BOT_TOKEN is not set')
    app=Application.builder().token(TOKEN).build(); app.add_handler(CommandHandler('start',start)); app.add_handler(CommandHandler('admin',start)); app.add_handler(CommandHandler('cancel',cancel)); app.add_handler(CallbackQueryHandler(cb)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,msg)); app.run_polling(allowed_updates=Update.ALL_TYPES)
