
ssh proxy1 "swift-init proxy restart; service memcached restart"
ssh proxy2 "swift-init proxy restart; service memcached restart"
