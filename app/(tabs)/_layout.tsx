import { Tabs } from 'expo-router';

import { CustomTabBar } from '@/src/components/CustomTabBar';

export default function TabLayout() {
  return (
    <Tabs
      tabBar={(props) => {
        const tabProps = props as unknown as {
          state: {
            index: number;
            routes: { key: string; name: string; params?: object }[];
          };
          navigation: {
            emit: (event: {
              type: string;
              target: string;
              canPreventDefault: boolean;
            }) => { defaultPrevented: boolean };
            navigate: (name: string, params?: object) => void;
          };
        };
        return <CustomTabBar state={tabProps.state} navigation={tabProps.navigation} />;
      }}
      screenOptions={{
        headerShown: false,
      }}
    >
      <Tabs.Screen name="news" options={{ title: '소식' }} />
      <Tabs.Screen name="games" options={{ title: '내 게임' }} />
      <Tabs.Screen name="index" options={{ title: '홈' }} />
      <Tabs.Screen name="ranking" options={{ title: '랭킹' }} />
      <Tabs.Screen name="settings" options={{ title: '설정' }} />
    </Tabs>
  );
}
