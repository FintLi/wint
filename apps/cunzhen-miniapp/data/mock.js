const mockState = {
  listings: [
    {
      id: 'L-001',
      title: '西乡地铁通勤友好单间',
      village: '西乡径贝新村',
      areaBand: '西乡',
      roomType: '单间',
      monthlyRent: 1280,
      depositRule: '押一付一',
      utilityRule: '水8电1.5，无额外管理费',
      floorLabel: '5楼',
      sunlight: '朝南，下午采光稳定',
      elevator: '无',
      furnitureAppliances: '床、空调、热水器、衣柜',
      moveInDate: '2026-03-12',
      lastVerifiedAt: '2026-03-09T11:00:00+08:00',
      videoUrl: 'https://example.com/cunzhen/L-001',
      sourceRole: '合作中介',
      sourceChannel: '私信邀约',
      status: '可发布',
      authFlag: '已认证',
      safetyTags: ['夜归主路', '无隐形杂费'],
      commuteTags: ['西乡上班', '45分钟内'],
      notes: '适合预算敏感、通勤优先租客',
      versions: [
        {
          version: '1.0',
          monthlyRent: 1280,
          moveInDate: '2026-03-12',
          contactSnapshot: '合作中介 A',
          utilityRule: '水8电1.5，无额外管理费',
          updatedAt: '2026-03-09T11:00:00+08:00'
        }
      ]
    },
    {
      id: 'L-002',
      title: '福永 1500 左右小一房',
      village: '福永白石厦',
      areaBand: '福永',
      roomType: '一房',
      monthlyRent: 1580,
      depositRule: '押一付一',
      utilityRule: '水7电1.3，卫生费 30',
      floorLabel: '4楼',
      sunlight: '窗户大，白天采光不错',
      elevator: '无',
      furnitureAppliances: '床、空调、洗衣机、油烟机',
      moveInDate: '2026-03-11',
      lastVerifiedAt: '2026-03-09T09:00:00+08:00',
      videoUrl: 'https://example.com/cunzhen/L-002',
      sourceRole: '二房东',
      sourceChannel: '合作转介绍',
      status: '可发布',
      authFlag: '待认证',
      safetyTags: ['独卫', '适合情侣', '夜间较安静'],
      commuteTags: ['机场周边', '性价比盘'],
      notes: '适合想从单间升级到一房的租客',
      versions: [
        {
          version: '1.0',
          monthlyRent: 1580,
          moveInDate: '2026-03-11',
          contactSnapshot: '包租方 B',
          utilityRule: '水7电1.3，卫生费 30',
          updatedAt: '2026-03-09T09:00:00+08:00'
        }
      ]
    },
    {
      id: 'L-003',
      title: '固戍近主路女生友好单间',
      village: '固戍下围园',
      areaBand: '固戍',
      roomType: '单间',
      monthlyRent: 1180,
      depositRule: '押一付一',
      utilityRule: '水8电1.5',
      floorLabel: '3楼',
      sunlight: '一般',
      elevator: '无',
      furnitureAppliances: '床、空调、热水器',
      moveInDate: '2026-03-15',
      lastVerifiedAt: '2026-03-06T10:00:00+08:00',
      videoUrl: 'https://example.com/cunzhen/L-003',
      sourceRole: '房东',
      sourceChannel: '私信邀约',
      status: '可发布',
      authFlag: '已认证',
      safetyTags: ['主路回家', '女生友好'],
      commuteTags: ['固戍上班', '预算 1200 左右'],
      notes: '该房源会因为超时自动进入失效提醒',
      versions: [
        {
          version: '1.0',
          monthlyRent: 1180,
          moveInDate: '2026-03-15',
          contactSnapshot: '房东 C',
          utilityRule: '水8电1.5',
          updatedAt: '2026-03-06T10:00:00+08:00'
        }
      ]
    },
    {
      id: 'L-004',
      title: '后瑞预算友好合租次卧',
      village: '后瑞南一巷',
      areaBand: '后瑞',
      roomType: '合租',
      monthlyRent: 980,
      depositRule: '押一付一',
      utilityRule: '',
      floorLabel: '2楼',
      sunlight: '一般',
      elevator: '无',
      furnitureAppliances: '床、空调',
      moveInDate: '2026-03-18',
      lastVerifiedAt: '2026-03-09T12:00:00+08:00',
      videoUrl: '',
      sourceRole: '拍房员',
      sourceChannel: '线下采集',
      status: '待核验',
      authFlag: '待认证',
      safetyTags: ['预算友好'],
      commuteTags: ['机场线'],
      notes: '演示不可发布的待补资料房源',
      versions: [
        {
          version: '0.9',
          monthlyRent: 980,
          moveInDate: '2026-03-18',
          contactSnapshot: '拍房员 D',
          utilityRule: '',
          updatedAt: '2026-03-09T12:00:00+08:00'
        }
      ]
    }
  ],
  leads: [
    {
      id: 'Q-001',
      createdAt: '2026-03-09T12:30:00+08:00',
      name: '阿杰',
      contact: 'wechat-ajjie',
      budgetMin: 1000,
      budgetMax: 1600,
      workArea: '西乡地铁站',
      commutePreference: '45 分钟内',
      roomPreference: '单间',
      moveInDeadline: '2026-03-14',
      sourceChannel: '短视频',
      status: '已匹配',
      priority: 'A',
      notes: '优先想看周三晚场'
    },
    {
      id: 'Q-002',
      createdAt: '2026-03-09T14:00:00+08:00',
      name: '小林',
      contact: 'wechat-lin',
      budgetMin: 1400,
      budgetMax: 2000,
      workArea: '机场东',
      commutePreference: '60 分钟内',
      roomPreference: '一房',
      moveInDeadline: '2026-03-22',
      sourceChannel: '朋友介绍',
      status: '新线索',
      priority: 'B',
      notes: '偏好独卫'
    }
  ],
  viewings: [
    {
      id: 'A-001',
      listingId: 'L-001',
      listingTitle: '西乡地铁通勤友好单间',
      leadName: '阿杰',
      contact: 'wechat-ajjie',
      preferredDate: '2026-03-12',
      timeSlot: '周三 19:30-22:00',
      status: '已确认',
      notes: '下班后直达'
    }
  ]
}

module.exports = {
  mockState
}
