const { REQUIRED_LISTING_FIELDS, EXPIRY_HOURS } = require('./constants')
const { hoursSince } = require('./format')

function hasValue(value) {
  return !(value === undefined || value === null || value === '')
}

function isListingPublishable(listing) {
  return REQUIRED_LISTING_FIELDS.every(function (field) {
    return hasValue(listing[field])
  })
}

function isListingExpired(listing) {
  return hoursSince(listing.lastVerifiedAt) > EXPIRY_HOURS
}

function deriveListingState(listing) {
  const publishable = isListingPublishable(listing)
  const expired = isListingExpired(listing)
  const state = Object.assign({}, listing)

  state.publishable = publishable
  state.expired = expired
  state.frontendVisible = publishable && !expired && listing.status === '可发布'
  state.verificationLabel = expired ? '已超 72 小时，需复核' : '72 小时内已核验'
  return state
}

function applyFilters(listings, filters) {
  return listings.filter(function (listing) {
    if (filters.areaBand && filters.areaBand !== '全部' && listing.areaBand !== filters.areaBand) {
      return false
    }
    if (filters.roomType && filters.roomType !== '全部' && listing.roomType !== filters.roomType) {
      return false
    }
    if (filters.elevator && filters.elevator !== '全部' && listing.elevator !== filters.elevator) {
      return false
    }
    if (!fitsBudget(listing.monthlyRent, filters.budget)) {
      return false
    }
    return true
  })
}

function fitsBudget(rent, budgetLabel) {
  if (!budgetLabel || budgetLabel === '全部') return true
  if (budgetLabel === '1000以下') return rent < 1000
  if (budgetLabel === '1000-1500') return rent >= 1000 && rent <= 1500
  if (budgetLabel === '1500-2000') return rent > 1500 && rent <= 2000
  if (budgetLabel === '2000-2500') return rent > 2000 && rent <= 2500
  return true
}

function latestVersion(listing) {
  if (!listing.versions || !listing.versions.length) return null
  return listing.versions[listing.versions.length - 1]
}

module.exports = {
  deriveListingState,
  isListingPublishable,
  isListingExpired,
  applyFilters,
  latestVersion
}
