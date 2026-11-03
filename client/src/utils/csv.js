// CSV export helpers. Free of Vue so any view can reuse them.

// A cell starting with one of these is treated as a formula by Excel and Google Sheets.
// Product names and locations are data we do not control, so without a guard a value like
// "=HYPERLINK(...)" would execute when the exported file is opened (CSV injection).
// Text cells that start with one are prefixed with an apostrophe, which spreadsheets
// show as a literal marker instead of evaluating.
const FORMULA_TRIGGERS = /^[=+\-@\t\r]/

function escapeCell(value) {
  if (value === null || value === undefined) return ''

  // Numbers are written as-is so spreadsheets keep them numeric. They also skip the
  // formula guard below, which would otherwise turn a negative number into text.
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : ''

  let text = String(value)
  if (FORMULA_TRIGGERS.test(text)) text = `'${text}`

  // RFC 4180: quote fields that contain a comma, quote or line break, and double any quotes.
  if (/[",\r\n]/.test(text)) text = `"${text.replace(/"/g, '""')}"`
  return text
}

/**
 * Build CSV text.
 * @param {Array} rows - source objects, one per line
 * @param {Array<{header: string, value: (row) => string|number|null}>} columns
 */
export function toCsv(rows, columns) {
  const header = columns.map(col => escapeCell(col.header)).join(',')
  const lines = rows.map(row => columns.map(col => escapeCell(col.value(row))).join(','))
  // CRLF line endings are what RFC 4180 specifies and what Excel expects.
  return [header, ...lines].join('\r\n') + '\r\n'
}

/** Trigger a browser download of CSV text. */
export function downloadCsv(filename, csv) {
  // The byte-order mark makes Excel detect UTF-8; without it Japanese text opens garbled.
  const blob = new Blob(['﻿', csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  // Revoke on the next tick so the download has already started when the URL goes away.
  setTimeout(() => URL.revokeObjectURL(url), 0)
}
