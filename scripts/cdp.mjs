// Minimal CDP client over Node 24's built-in WebSocket. Attaches to an already-open
// (user-authenticated) Chrome tab via --remote-debugging-port=9222. No credentials handled here.
// Usage:
//   node scripts/cdp.mjs targets
//   node scripts/cdp.mjs nav <url>
//   node scripts/cdp.mjs shot <outfile.png>
//   node scripts/cdp.mjs text                 # visible innerText of the page
//   node scripts/cdp.mjs eval '<js expr>'     # evaluate JS in page, print JSON result
const BASE = `http://127.0.0.1:${process.env.CDP_PORT || 9222}`

async function firstPage() {
  const list = await (await fetch(`${BASE}/json`)).json()
  const pages = list.filter(t => t.type === 'page' && t.webSocketDebuggerUrl)
  if (!pages.length) throw new Error('no page targets')
  return pages[0]
}

function connect(wsUrl) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(wsUrl)
    ws.onopen = () => res(ws)
    ws.onerror = (e) => rej(new Error('ws error: ' + (e.message || e)))
  })
}

let _id = 0
function send(ws, method, params = {}) {
  const id = ++_id
  return new Promise((res, rej) => {
    const onMsg = (ev) => {
      const m = JSON.parse(ev.data)
      if (m.id === id) { ws.removeEventListener('message', onMsg); m.error ? rej(new Error(m.error.message)) : res(m.result) }
    }
    ws.addEventListener('message', onMsg)
    ws.send(JSON.stringify({ id, method, params }))
  })
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms))

const [cmd, arg] = process.argv.slice(2)
const page = await firstPage()
if (cmd === 'targets') {
  const list = await (await fetch(`${BASE}/json`)).json()
  console.log(list.filter(t => t.type === 'page').map(t => `${t.title} :: ${t.url}`).join('\n'))
  process.exit(0)
}
const ws = await connect(page.webSocketDebuggerUrl)
await send(ws, 'Page.enable'); await send(ws, 'Runtime.enable')

if (cmd === 'nav') {
  await send(ws, 'Page.navigate', { url: arg })
  await sleep(3500)
  console.log('navigated to', arg)
} else if (cmd === 'shot') {
  const { data } = await send(ws, 'Page.captureScreenshot', { format: 'png' })
  const { writeFileSync } = await import('node:fs')
  writeFileSync(arg, Buffer.from(data, 'base64'))
  console.log('saved', arg)
} else if (cmd === 'text') {
  const { result } = await send(ws, 'Runtime.evaluate', {
    expression: 'document.body.innerText.slice(0, 12000)', returnByValue: true,
  })
  console.log(result.value)
} else if (cmd === 'eval') {
  const { result } = await send(ws, 'Runtime.evaluate', { expression: arg, returnByValue: true })
  console.log(JSON.stringify(result.value, null, 2))
}
ws.close()
process.exit(0)
