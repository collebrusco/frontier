// Frontier: TFMG (industrial blasting -> molten -> casting) is the canonical
// steel source. Strip every other mod's steel-ingot recipe so cheap mixes
// (e.g. createnuclear's unheated coal+iron) can't bypass the blast furnace.
ServerEvents.recipes(event => {
  const removed = []
  event.forEachRecipe({ output: '#c:ingots/steel' }, r => {
    const id = r.getId().toString()
    const out = r.json.has('result')
      ? r.json.get('result').toString()
      : r.json.toString()
    if (!out.includes('tfmg:steel_ingot')) {
      event.remove({ id })
      removed.push(`${id} (${out})`)
    }
  })
  console.log(`[frontier] disabled ${removed.length} non-TFMG steel ingot recipes`)
  removed.forEach(s => console.log(`  - ${s}`))
})
