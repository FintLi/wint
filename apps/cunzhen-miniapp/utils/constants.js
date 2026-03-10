const REQUIRED_LISTING_FIELDS = ['monthlyRent', 'utilityRule', 'lastVerifiedAt', 'videoUrl']
const EXPIRY_HOURS = 72
const LISTING_STATUSES = ['待核验', '可发布', '已预约', '已成交', '已失效']
const LEAD_STATUSES = ['新线索', '已联系', '已匹配', '已带看', '已成交', '流失']
const VIEWING_STATUSES = ['待确认', '已确认', '已完成', '爽约']
const ROOM_TYPES = ['全部', '单间', '合租', '一房']
const AREA_BANDS = ['全部', '西乡', '固戍', '后瑞', '福永']
const ELEVATOR_OPTIONS = ['全部', '有', '无']
const BUDGET_OPTIONS = ['全部', '1000以下', '1000-1500', '1500-2000', '2000-2500']
const COMMUTE_OPTIONS = ['30 分钟内', '45 分钟内', '60 分钟内']
const TIME_SLOTS = ['周三 19:30-22:00', '周六 14:00-18:00', '自定义沟通']

module.exports = {
  REQUIRED_LISTING_FIELDS,
  EXPIRY_HOURS,
  LISTING_STATUSES,
  LEAD_STATUSES,
  VIEWING_STATUSES,
  ROOM_TYPES,
  AREA_BANDS,
  ELEVATOR_OPTIONS,
  BUDGET_OPTIONS,
  COMMUTE_OPTIONS,
  TIME_SLOTS
}
