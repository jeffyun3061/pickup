const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// 백엔드/관리자·pytest 임시 디렉터리는 Metro watch 대상에서 제외
// (ENOENT: watch 'server/pytest-cache-files-*' 크래시 방지)
const root = __dirname;
const block = [
  path.resolve(root, 'server'),
  path.resolve(root, 'admin'),
  path.resolve(root, 'design-ref'),
  path.resolve(root, 'docs'),
].map((p) => p.replace(/[/\\]/g, '[/\\\\]'));

config.resolver.blockList = [
  ...(Array.isArray(config.resolver.blockList)
    ? config.resolver.blockList
    : config.resolver.blockList
      ? [config.resolver.blockList]
      : []),
  new RegExp(`^(${block.join('|')})([/\\\\].*)?$`),
];

module.exports = config;
