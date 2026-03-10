function pad(value) {
  return value < 10 ? '0' + value : '' + value
}

function formatCurrency(value) {
  if (value === null || value === undefined || value === '') return '--'
  return '¥' + value + '/月'
}

function formatDate(dateLike) {
  if (!dateLike) return '--'
  const date = new Date(dateLike)
  if (Number.isNaN(date.getTime())) return '--'
  return [date.getFullYear(), pad(date.getMonth() + 1), pad(date.getDate())].join('-')
}

function hoursSince(dateLike) {
  if (!dateLike) return Number.POSITIVE_INFINITY
  const time = new Date(dateLike).getTime()
  if (Number.isNaN(time)) return Number.POSITIVE_INFINITY
  return (Date.now() - time) / (1000 * 60 * 60)
}

function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

function formatVersionTag(version) {
  if (!version) return 'v1'
  return 'v' + version
}

module.exports = {
  formatCurrency,
  formatDate,
  hoursSince,
  clone,
  formatVersionTag
}
