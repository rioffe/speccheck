-- docs/title-from-h1.lua -- promote the document's first level-1 heading to pandoc's `title`
-- metadata and drop it from the body, so the HTML build gets a proper <title> and title block
-- while the Markdown source keeps its H1 for GitHub and the PDF, and the table of contents
-- lists only the sections (H2/H3), not the article's own name.
local title_set = false

function Header(el)
  if el.level == 1 and not title_set then
    title_set = true
    TITLE = pandoc.MetaInlines(el.content)
    return {}
  end
end

function Meta(meta)
  if TITLE ~= nil and meta.title == nil then
    meta.title = TITLE
  end
  return meta
end

-- Run Header before Meta (pandoc walks blocks first, then metadata, when the filter is a
-- single table; make the order explicit).
return { { Header = Header }, { Meta = Meta } }
