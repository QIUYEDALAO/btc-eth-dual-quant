# M0 Dual-Source Audit Diagnostics

- Status: blocked
- Generated UTC: 2026-07-09T21:59:14+00:00
- Scope: official public REST versus official public ZIP evidence only
- API key used: no
- Private data used: no
- Private smoke rerun: no
- VPN/proxy/region bypass used: no
- Raw payload committed: no
- Trading approval: no

## Execution Nodes

| Logical node | Generated UTC | Planned scopes | Completed scopes | Passed scopes |
| --- | --- | ---: | ---: | ---: |
| `local` | `2026-07-09T21:48:19+00:00` | 95 | 95 | 29 |
| `remote` | `2026-07-09T21:59:14+00:00` | 62 | 62 | 0 |

## Scope Evidence

| Node | Dataset | Symbol | Month | Reasons | REST | ZIP | REST rows | ZIP rows | Overlap | REST-only | ZIP-only | Exact | Format | Boundary | Revision | Timestamp | Invalid | Status | REST SHA256 | ZIP SHA256 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `local` | `spot_klines` | `BTCUSDT` | `2019-09` | `first` | 200 | 200 | 720 | 720 | 720 | 0 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | pass | `7f9518a8c7bab88166a33a1e1901ce37e0471f677c8181cd537b35b9150a5866` | `2aaaf6e4d0455b889225ca1cfde23a15e2359850f803bc9998df30ac1bbef63f` |
| `local` | `spot_klines` | `BTCUSDT` | `2019-11` | `gap` | 200 | 200 | 716 | 716 | 716 | 0 | 0 | 716 | 0 | 0 | 0 | 0 | 0 | pass | `b25a3704310f7f336d8a516ff2aa9781953299ebdc304bcbdec986abf4e837a3` | `63572600e87350f1d5679049a44e8338cf7b692d0c67220dc316267a91af108b` |
| `local` | `spot_klines` | `BTCUSDT` | `2020-02` | `gap` | 200 | 200 | 690 | 690 | 690 | 0 | 0 | 690 | 0 | 0 | 0 | 0 | 0 | pass | `2e1fa0a3efb81158e43f6364fca8e41f26144988f42de7bb4ad7d4e0364e3b46` | `0189065a1b789825448530cb3fdddcefa45ca13b0a6bca181f358c72d3a6d5e6` |
| `local` | `spot_klines` | `BTCUSDT` | `2020-03` | `anomaly,gap` | 200 | 200 | 743 | 743 | 743 | 0 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | pass | `c5f7ed10ef389fd1c8b7cbc6cf79ceb4f5d90768c6dc88f6392aa96aa994347b` | `cc36c481c31ef93115d96b5a7045ec2ef737e5339546d6688cb1f677526c6787` |
| `local` | `spot_klines` | `BTCUSDT` | `2020-04` | `gap` | 200 | 200 | 718 | 718 | 718 | 0 | 0 | 718 | 0 | 0 | 0 | 0 | 0 | pass | `960dd6d29e39a6548adc48ad3775800a2830a02da57201d38d44757d02f3c44e` | `4f08d13c81cadf8d5fc7afcd0924d084d2f81c7d004323812e7508ad135f89e7` |
| `local` | `spot_klines` | `BTCUSDT` | `2020-06` | `gap` | 200 | 200 | 717 | 717 | 717 | 0 | 0 | 717 | 0 | 0 | 0 | 0 | 0 | pass | `732190bfb0f03e9c26dc06d0a27e487c400300a275e9a2df9365afda47117dbf` | `2ccf45a7307e09dec1fd3622d54057e7e44371bf70a8be1030687f654341799e` |
| `local` | `spot_klines` | `BTCUSDT` | `2020-11` | `gap` | 200 | 200 | 719 | 719 | 719 | 0 | 0 | 719 | 0 | 0 | 0 | 0 | 0 | pass | `daf719a4ce2995ac6a559edb0d36d2ce8e98427da1342caef6e9d7eaaa131574` | `c3f3548fd082f0fa63d2138a5aca3b572729f6351de8a20c895a80acd3ae395b` |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `anomaly,gap` | 200 | 200 | 739 | 740 | 739 | 0 | 1 | 738 | 0 | 0 | 8 | 1 | 0 | blocked | `56a0411142029e81ec2adb3e80dfcd5b939ca53b659eb07c473b558a62777d03` | `c880c8e76e2dbcbed04bc1ddd549949a94a4314520dc1f1becbd881453aa5ede` |
| `local` | `spot_klines` | `BTCUSDT` | `2021-02` | `anomaly,gap` | 200 | 200 | 671 | 671 | 671 | 0 | 0 | 671 | 0 | 0 | 0 | 0 | 0 | pass | `d6c0cff81b36f0b8ab90be274790c6ca798692f430b49ee586b2b0ef4fc8f7f3` | `8cd20f5058dc7585cfa874a3ab0e5fd0096f369c182d8fda80dc16495050e018` |
| `local` | `spot_klines` | `BTCUSDT` | `2021-03` | `gap` | 200 | 200 | 743 | 743 | 743 | 0 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | pass | `552cf128f9232746228a21e0a307f37f4934ddc77b41ceb8f8f607830c03ec24` | `748783e9715835dd334fbc0cbbff0518962ebbcbe0430acb65f2f506193bad2d` |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `gap` | 200 | 200 | 715 | 715 | 715 | 0 | 0 | 714 | 0 | 0 | 6 | 0 | 0 | blocked | `e85de2a38f44716013ad67960f1f1c0b74137f4da2e481346fd7d7b8e668ba88` | `e5a33803814e6771c4c85e8f2e28e90e46d40f14ca3180a8c10c305cf07fab74` |
| `local` | `spot_klines` | `BTCUSDT` | `2021-08` | `gap` | 200 | 200 | 740 | 740 | 740 | 0 | 0 | 740 | 0 | 0 | 0 | 0 | 0 | pass | `1b5fb1eb040c330ce7271190c6ff14a8a133db1c8f00097318bfb4381d999b21` | `5cadb462255761842326a2c4b5fe2a91c8a2135c3ba6dd5f0969877f0722f4be` |
| `local` | `spot_klines` | `BTCUSDT` | `2021-09` | `gap` | 200 | 200 | 718 | 718 | 718 | 0 | 0 | 718 | 0 | 0 | 0 | 0 | 0 | pass | `ab6c437a4c4c70d8a9c5c79a09568cb5f8bf47b3ecf3075ce73813997afaed38` | `0d344f8ab39d910c148b89fada91256afcb3e8b20eb812ebc158ac8ac527ea07` |
| `local` | `spot_klines` | `BTCUSDT` | `2023-02` | `middle` | 200 | 200 | 672 | 672 | 672 | 0 | 0 | 672 | 0 | 0 | 0 | 0 | 0 | pass | `8ad99a55cfe6c17ad87e34beb048c4e1985bf86b378a7b26cd4d249b653ef34e` | `53525b700548a19488fcb8754778acdf7941c9ba0b6e7eb548a51a376ef8d86b` |
| `local` | `spot_klines` | `BTCUSDT` | `2023-03` | `anomaly,gap` | 200 | 200 | 743 | 743 | 743 | 0 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | pass | `32bd924ae20b7069b0e763065b635774c3eeb6170bd7f1edeecd76b124a121eb` | `7f2afb8e0179a57ac31eab5205660298ba5eb77039ac2e21aef9b715ff3d06ce` |
| `local` | `spot_klines` | `BTCUSDT` | `2026-06` | `latest_complete` | 200 | 200 | 720 | 720 | 720 | 0 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | pass | `983eb19654eb743ecd11e2bc052977402dbd761a1bfc6d5222febffefaeb4866` | `7c446aee297f382ee92b8d9b3300a1d7c21bed8166118f3bb261275bed5e308e` |
| `local` | `um_futures_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `512a1d725c8df97a1bbbee4f118e730e9628500a8f271c9e59d2a7fc5fbfcfcc` |
| `local` | `um_futures_klines` | `BTCUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9fc0c560cce35fd083febee10c0c8c3ffcd56a9185f9b489f265a51bbf60ec6e` |
| `local` | `um_futures_klines` | `BTCUSDT` | `2021-07` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `97241c02191fd4694daf9836269e6f8ed04ef5bf858414de5a3354678552b54d` |
| `local` | `um_futures_klines` | `BTCUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `ed6f0a84d1b2ed8f73fbdd4df10703e2ab49864fc4d657b0d8a9464a49dd4a29` |
| `local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `e3dcb9fe9d70fea19dfbdc5294044da69b9061c6f7411e99468825fac1ce8d61` |
| `local` | `um_futures_klines` | `BTCUSDT` | `2026-06` | `latest_complete` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `30bba473837a672a6a00a181a447446852414e6927bbda6684f873571788e9aa` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `0c53176e13066f16c36ae12fe2cd78389cdbd56d11fe8cf49c086976befa106d` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `cbaf3993eb744aed603e271a0e184c946fd8d09e62b8af53e55d03211f3d9e94` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2021-06` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `582c1e1c0928949e7b916a1685894b90f3b1afd8db8861f062fdb55456ceac4e` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `569b41a00797933a3e2dd9ceaed3e2d4f7bc0526ce2dd06d1190835732958ca7` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2022-07` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `baafc36bfebd44d4356b8c5cae3a92dba09e03a841e7ef13a358ebe6960e4903` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2022-08` | `gap` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `1925c38ceee17ea2142ce019f360db7c8549bc39998bb1bd63fc2027df5712bb` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9804dbd86adbd447d60edf955fd668de3e426fa3c6596a13d69ae539a2549864` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f15d23370f252082d8741819800b82f62ac8bbc9001b53ab6abb5d65ccb3ed3d` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c12b3fc18d15bb91005493e6afedb49a6c776ff821e7fe607c87f41f7747d70e` |
| `local` | `mark_price_klines` | `BTCUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `7d1d36168726c482372301b51ac2b035a974a82b6ece309c3dbcd196b872edba` |
| `local` | `index_price_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `be084cf8e23e269f71648ea12db47a4b820ed2bb5bb39568fe6c46f5990c91aa` |
| `local` | `index_price_klines` | `BTCUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `d68a56741e00999d035d559d41819dd041aca5ae55f517f6cdf141b09df1464f` |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-04` | `gap` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c7fc797f71b3fd888427f7f7899ee903b6792bebdd6a34ac72382e84114f9c0f` |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `gap` | n/a | 200 | 0 | 600 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `910b71b3d4e913c9e598f00a889622f1950027c0c796455d921777b18ce4fa17` |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-08` | `gap` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `88566cdc570f17f3fade90fc43b25fb0855b87db516c4bf4456966ebc894c69a` |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `0feda6862c390c5435262d0451e796f972147edd62e48354bfcee0aa850fb72e` |
| `local` | `index_price_klines` | `BTCUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f9603cb938d32b611e113288977c245f4aff1e1b53c9e3a765e4e2c4b58165f0` |
| `local` | `index_price_klines` | `BTCUSDT` | `2023-04` | `gap,middle` | n/a | 200 | 0 | 672 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `32b9b99bb71347d6923bb3f76b67b343bc20e61292d12b4a9b9711bab3baf819` |
| `local` | `index_price_klines` | `BTCUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `360068164184b736bad620bf11b0583431400734b5258ccecbdb2fd5712142b5` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `32908c64c74ad4a74f4467a4918267e8e3ffa36d26ddf1d3c2cfe3e55a1b807a` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2020-12` | `gap` | n/a | 200 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `e8aa51ba4ab4b823521b0a40733f8b730221474e21f4bca021869a1239164d45` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2021-06` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `8fa833e63c39fb99478ea3216a346b6045ad41f4c227367dd3a840ba5a805678` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f840ce041c31117d3f46440cffaff53788b4362bb41e284c460ddc014b92ee1a` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `4710fe1875f28ab6d049c5a9e8910cbcca2bccbaaebadcaa408e52b13e477795` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `7ee49ca3276fd709a081c93d1d6531feec21f040f5b95baa9a5bc4e6c63712bb` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `5efd06f0fac2a28549b3c12cdd77d94420100717a681d5de8f7d6af11847a45b` |
| `local` | `premium_index_klines` | `BTCUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c3c2afc2206d6729812d99a7fc0ae909a6eb20cb5d01324d956612ff28b8c378` |
| `local` | `spot_klines` | `ETHUSDT` | `2019-09` | `first` | 200 | 200 | 720 | 720 | 720 | 0 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | pass | `eb3ffed3980c80376619fbb0bd9a87b9cb25b5a77b16f0ed6666b6c70c9a4628` | `4c2f8e47ac294e8f10726273b5a637ed172e98711915960eb5d15e71421d1ea7` |
| `local` | `spot_klines` | `ETHUSDT` | `2019-11` | `gap` | 200 | 200 | 716 | 716 | 716 | 0 | 0 | 716 | 0 | 0 | 0 | 0 | 0 | pass | `cf870adbfed2f040266667c56b854e2afbd19331d683e758e504be77478bec36` | `222067844687455cf1f50022f906eb19eb0001e690378f3c5a12e89dd7bdc721` |
| `local` | `spot_klines` | `ETHUSDT` | `2020-02` | `gap` | 200 | 200 | 690 | 690 | 690 | 0 | 0 | 690 | 0 | 0 | 0 | 0 | 0 | pass | `2ef603f8f089039c59b0d319c0bcd436565720bf0af05f01bb3a2004ae42b44e` | `1cf8a5b129d16bed072c46e158b5914247007ec7e00b489880f422c80c73afbe` |
| `local` | `spot_klines` | `ETHUSDT` | `2020-03` | `anomaly,gap` | 200 | 200 | 743 | 743 | 743 | 0 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | pass | `fcaa3505068e695f83f4cc7a21d4157df200bf76ce9850119fea6664df0d1bd1` | `2d80640a11d7de0eb052637d25aa95eb42602a927ad7c0be6d77a7689fbe93d3` |
| `local` | `spot_klines` | `ETHUSDT` | `2020-04` | `gap` | 200 | 200 | 718 | 718 | 718 | 0 | 0 | 718 | 0 | 0 | 0 | 0 | 0 | pass | `53aca10d5280aa276ab42336572fd0f90b54d52fe898c8b11fc147c90ea8ee29` | `0171b734b6131a542d79e35dc2ffbf886c1353574ef0983e95c4a8eb2856e56a` |
| `local` | `spot_klines` | `ETHUSDT` | `2020-06` | `gap` | 200 | 200 | 717 | 717 | 717 | 0 | 0 | 717 | 0 | 0 | 0 | 0 | 0 | pass | `1a6c9b95259edc7f85dad08010664f86f7f2010feb3671cc6fd493c336240e4c` | `d605f9ad1cc5556cfef7559f2d9e5cda0e55deba7f8ec03ea253bf8ec2f99d81` |
| `local` | `spot_klines` | `ETHUSDT` | `2020-11` | `gap` | 200 | 200 | 719 | 719 | 719 | 0 | 0 | 719 | 0 | 0 | 0 | 0 | 0 | pass | `4a6d4d822252dfc792f6bb77cf5a94c004c1ec06ff542a27b46df84d5f883c1f` | `a1b583dd091363fa1375bced29f78f69889c6da219d1c136b9d0f9269a19158b` |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `anomaly,gap` | 200 | 200 | 739 | 740 | 739 | 0 | 1 | 738 | 0 | 0 | 8 | 1 | 0 | blocked | `4ba0dc635afce3ddd952da51918e111f0d611e3b4f6f561182a38dba25dfe9ed` | `3928cbf56a66752d619eb438b92e0bc8cca2c8f0420237e5f5e81fdc19db13ea` |
| `local` | `spot_klines` | `ETHUSDT` | `2021-02` | `anomaly,gap` | 200 | 200 | 671 | 671 | 671 | 0 | 0 | 671 | 0 | 0 | 0 | 0 | 0 | pass | `45c220b03a964e6ef016c30d0e1e5695ad8fbe13112d50d143222657525e9b4e` | `f2e871ec862f36045bfa06a05210832d6b772a101a62b18bc7acddf906083b44` |
| `local` | `spot_klines` | `ETHUSDT` | `2021-03` | `gap` | 200 | 200 | 743 | 743 | 743 | 0 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | pass | `831aa218acbe9e61f972851ef1bcfefae60710efd67551ac6256b656ad91b5e8` | `64d15bc69f1788ccfa775cea47bf2f614a2ccb4eccf66257f512c8cd99d497ad` |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `gap` | 200 | 200 | 715 | 715 | 715 | 0 | 0 | 714 | 0 | 0 | 6 | 0 | 0 | blocked | `8cbc8fb115c13f5060de68ceb8553398637c500f19b26a1f19e55dca3c70b529` | `299b928009158743a92860a66c75ba898243ecbdfa8ef9b346c0a7fd553bcbff` |
| `local` | `spot_klines` | `ETHUSDT` | `2021-05` | `anomaly` | 200 | 200 | 744 | 744 | 744 | 0 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | pass | `84bf8010ea5e2b59248da33eced72109962b121cc480d0e33cd73e76ccfb6ba9` | `56707e7dbceacc194a6ecd31ea2b2a75a5c5f428182e63055217188c7e47c89d` |
| `local` | `spot_klines` | `ETHUSDT` | `2021-08` | `gap` | 200 | 200 | 740 | 740 | 740 | 0 | 0 | 740 | 0 | 0 | 0 | 0 | 0 | pass | `d872f04d564443be8cdcf0cf11f73f37c118a21295f9e111d543dabb44d64f89` | `9e390848fe76625e72b8f4eac86d405ed33c79ca9d79d9af14266c54d9d215af` |
| `local` | `spot_klines` | `ETHUSDT` | `2021-09` | `gap` | 200 | 200 | 718 | 718 | 718 | 0 | 0 | 718 | 0 | 0 | 0 | 0 | 0 | pass | `ab0f79fd95f76e4093a6d02bebb4c37db24010019e173da0bafd10b4026c3343` | `c10a61248a5c92280e35beadcfdf33220fdc0561ab1973893a4fe5a3335d3b78` |
| `local` | `spot_klines` | `ETHUSDT` | `2023-02` | `middle` | 200 | 200 | 672 | 672 | 672 | 0 | 0 | 672 | 0 | 0 | 0 | 0 | 0 | pass | `1a7fb957ec7e1b5cc83d22c1ac3fd85a73e3a9a93e0117b6850fde56a23f9c9c` | `c23f2ce377caba0279a932cfea93701bd02c996879293c5c395eaba06a943039` |
| `local` | `spot_klines` | `ETHUSDT` | `2023-03` | `anomaly,gap` | 200 | 200 | 743 | 743 | 743 | 0 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | pass | `571a112940b9c5d3295f6e40e64a3a2d4795ed0dfda4578305814ca4d8b530e1` | `90d268be1e0d39f7411f88ca3c0f21fe110fee7ff3c1dd054555e1fea6e22d8d` |
| `local` | `spot_klines` | `ETHUSDT` | `2026-06` | `latest_complete` | 200 | 200 | 720 | 720 | 720 | 0 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | pass | `e44290550dd619f85dc6b882bea38759f7c83674322f930a849836468c792ff2` | `e24954ab4ada9dc5f6bbf9ac30275d459a5729fb522f045f627296b4ad7ee985` |
| `local` | `um_futures_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `fb4840ec9ce7248ec4d82ce4bf3e9ca50872a3ad6b6ab4e3720f218f5f3a6021` |
| `local` | `um_futures_klines` | `ETHUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `36628b7275a7141048a7abbf8944ac07c9230fd055e81ff9d11beb1c229a6cd6` |
| `local` | `um_futures_klines` | `ETHUSDT` | `2021-05` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `e43c840fdde7903f99fcbc1311e75cd6cc58b4c302c48a017100747922eefd8c` |
| `local` | `um_futures_klines` | `ETHUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `4ac96035c3867e0bfeff4f2f526812ee4b73a0b87b3962bb40934e2614917395` |
| `local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `b4cda93568426a315e1de2fc7ca0ffb56586495680b233ffd7ce6bec11d18713` |
| `local` | `um_futures_klines` | `ETHUSDT` | `2026-06` | `latest_complete` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `138bcb6c7c8be4c5bdd8048fa417be551fbeffe4024f64e5bef5ed30d3069d8c` |
| `local` | `mark_price_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f513b4f388ae4bf94734cdc21256e5b7a4d7585928190ebc3704bab7076e1104` |
| `local` | `mark_price_klines` | `ETHUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `a11b0c3d7f69a3b0e52290144063f720a7152e63e47a55205fbdeb4bdde9b75f` |
| `local` | `mark_price_klines` | `ETHUSDT` | `2021-05` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `74c0131b01e5bb2d9df34995f06c12b201504f9da7b1906986fc153369cfcb37` |
| `local` | `mark_price_klines` | `ETHUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `95311f377e0ec8ef14e2c8c81599760b03a5f97dee3d1128c8d5077d29d2c2b1` |
| `local` | `mark_price_klines` | `ETHUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `47b99057e2ea8bda8a6d266a34066b8c23954c4b1fb2a21d29f3697b2f69358d` |
| `local` | `mark_price_klines` | `ETHUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `7627d0f3176e6819455c8ba6a963178bc93f512dbd63cd396d1ecf5699bf76e0` |
| `local` | `mark_price_klines` | `ETHUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f3321778da750ed4a24ce9907af8956dadd6bf022832b1d54594159ef923100b` |
| `local` | `index_price_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `77d4c9cf8917857fd064dc97e41267c199f3483331bf00520a3711b237f84fdc` |
| `local` | `index_price_klines` | `ETHUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9aff667c1b4bcdf7cad32f11cecca0c98a713abe532fe3b05fc126ec06280fd0` |
| `local` | `index_price_klines` | `ETHUSDT` | `2021-05` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `31dc1cbbf5971fd5b96174e89bf94dc42d86bc3ddfe80af4a5798045256b520d` |
| `local` | `index_price_klines` | `ETHUSDT` | `2022-07` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `ba71f1c9474e1b729be5f6ede7a597f1c4f1805d5f9b6ef8b426af49fab92daf` |
| `local` | `index_price_klines` | `ETHUSDT` | `2022-08` | `gap` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `d48d8deb71deacc0f44066cee209dc54b23a1cb694ea2cbd187c7a106361a522` |
| `local` | `index_price_klines` | `ETHUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `58b6b569c0c109a32f8d1e592aaf64698b287e3e9bd6bdbd3a2a9ab1f7fe0ae0` |
| `local` | `index_price_klines` | `ETHUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `79b89a55307308d21c24d3116eba7a80256a2cf4ec2d91866993479b36a77b48` |
| `local` | `index_price_klines` | `ETHUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `8123796c52220fbd26041765f9bb398bd39f6953b3104fddad3d79c32b15786f` |
| `local` | `index_price_klines` | `ETHUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `df7687e94af210003e030fd710c9841843522a84c6442fe6d536f3487f15c790` |
| `local` | `premium_index_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `0014c873b652a617695443046b66f3254a128b0700fe324045ed8e5ac2bc9ee8` |
| `local` | `premium_index_klines` | `ETHUSDT` | `2020-12` | `gap` | n/a | 200 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `01cbc0c45ce59f68dc4151fc3db413303753658468fbc3753b8b153d5b27b4b5` |
| `local` | `premium_index_klines` | `ETHUSDT` | `2021-06` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `99a950351a0d6c23bb673e20c6ff7c39fc8426ee0718c963bccd331e374945e2` |
| `local` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `a600a686be980286a511f3eb22eb5f0b88042e56c3e643bfa926e21c17aeb706` |
| `local` | `premium_index_klines` | `ETHUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c746daaa27bab64d0c65db7309cdf4bd59e214508f0cff0740acd9b3c258ad78` |
| `local` | `premium_index_klines` | `ETHUSDT` | `2023-04` | `gap,middle` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `46a7e5d131a86bccf157ca10ec0c26579d9ec0025d4a61ad1370bc3b131595d1` |
| `local` | `premium_index_klines` | `ETHUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9c5b050a3b928e39ffd1badaefd56c2092751e78e2e6b1c2c03953f58a7c709f` |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `512a1d725c8df97a1bbbee4f118e730e9628500a8f271c9e59d2a7fc5fbfcfcc` |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9fc0c560cce35fd083febee10c0c8c3ffcd56a9185f9b489f265a51bbf60ec6e` |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2021-07` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `97241c02191fd4694daf9836269e6f8ed04ef5bf858414de5a3354678552b54d` |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `ed6f0a84d1b2ed8f73fbdd4df10703e2ab49864fc4d657b0d8a9464a49dd4a29` |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `e3dcb9fe9d70fea19dfbdc5294044da69b9061c6f7411e99468825fac1ce8d61` |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2026-06` | `latest_complete` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `30bba473837a672a6a00a181a447446852414e6927bbda6684f873571788e9aa` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `0c53176e13066f16c36ae12fe2cd78389cdbd56d11fe8cf49c086976befa106d` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `cbaf3993eb744aed603e271a0e184c946fd8d09e62b8af53e55d03211f3d9e94` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2021-06` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `582c1e1c0928949e7b916a1685894b90f3b1afd8db8861f062fdb55456ceac4e` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `569b41a00797933a3e2dd9ceaed3e2d4f7bc0526ce2dd06d1190835732958ca7` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2022-07` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `baafc36bfebd44d4356b8c5cae3a92dba09e03a841e7ef13a358ebe6960e4903` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2022-08` | `gap` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `1925c38ceee17ea2142ce019f360db7c8549bc39998bb1bd63fc2027df5712bb` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9804dbd86adbd447d60edf955fd668de3e426fa3c6596a13d69ae539a2549864` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f15d23370f252082d8741819800b82f62ac8bbc9001b53ab6abb5d65ccb3ed3d` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c12b3fc18d15bb91005493e6afedb49a6c776ff821e7fe607c87f41f7747d70e` |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `7d1d36168726c482372301b51ac2b035a974a82b6ece309c3dbcd196b872edba` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `be084cf8e23e269f71648ea12db47a4b820ed2bb5bb39568fe6c46f5990c91aa` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `d68a56741e00999d035d559d41819dd041aca5ae55f517f6cdf141b09df1464f` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-04` | `gap` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c7fc797f71b3fd888427f7f7899ee903b6792bebdd6a34ac72382e84114f9c0f` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-07` | `gap` | n/a | 200 | 0 | 600 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `910b71b3d4e913c9e598f00a889622f1950027c0c796455d921777b18ce4fa17` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-08` | `gap` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `88566cdc570f17f3fade90fc43b25fb0855b87db516c4bf4456966ebc894c69a` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `0feda6862c390c5435262d0451e796f972147edd62e48354bfcee0aa850fb72e` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f9603cb938d32b611e113288977c245f4aff1e1b53c9e3a765e4e2c4b58165f0` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2023-04` | `gap,middle` | n/a | 200 | 0 | 672 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `32b9b99bb71347d6923bb3f76b67b343bc20e61292d12b4a9b9711bab3baf819` |
| `remote` | `index_price_klines` | `BTCUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `360068164184b736bad620bf11b0583431400734b5258ccecbdb2fd5712142b5` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `32908c64c74ad4a74f4467a4918267e8e3ffa36d26ddf1d3c2cfe3e55a1b807a` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2020-12` | `gap` | n/a | 200 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `e8aa51ba4ab4b823521b0a40733f8b730221474e21f4bca021869a1239164d45` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2021-06` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `8fa833e63c39fb99478ea3216a346b6045ad41f4c227367dd3a840ba5a805678` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f840ce041c31117d3f46440cffaff53788b4362bb41e284c460ddc014b92ee1a` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `4710fe1875f28ab6d049c5a9e8910cbcca2bccbaaebadcaa408e52b13e477795` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `7ee49ca3276fd709a081c93d1d6531feec21f040f5b95baa9a5bc4e6c63712bb` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `5efd06f0fac2a28549b3c12cdd77d94420100717a681d5de8f7d6af11847a45b` |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c3c2afc2206d6729812d99a7fc0ae909a6eb20cb5d01324d956612ff28b8c378` |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `fb4840ec9ce7248ec4d82ce4bf3e9ca50872a3ad6b6ab4e3720f218f5f3a6021` |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `36628b7275a7141048a7abbf8944ac07c9230fd055e81ff9d11beb1c229a6cd6` |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2021-05` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `e43c840fdde7903f99fcbc1311e75cd6cc58b4c302c48a017100747922eefd8c` |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `4ac96035c3867e0bfeff4f2f526812ee4b73a0b87b3962bb40934e2614917395` |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `b4cda93568426a315e1de2fc7ca0ffb56586495680b233ffd7ce6bec11d18713` |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2026-06` | `latest_complete` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `138bcb6c7c8be4c5bdd8048fa417be551fbeffe4024f64e5bef5ed30d3069d8c` |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f513b4f388ae4bf94734cdc21256e5b7a4d7585928190ebc3704bab7076e1104` |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `a11b0c3d7f69a3b0e52290144063f720a7152e63e47a55205fbdeb4bdde9b75f` |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2021-05` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `74c0131b01e5bb2d9df34995f06c12b201504f9da7b1906986fc153369cfcb37` |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `95311f377e0ec8ef14e2c8c81599760b03a5f97dee3d1128c8d5077d29d2c2b1` |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `47b99057e2ea8bda8a6d266a34066b8c23954c4b1fb2a21d29f3697b2f69358d` |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `7627d0f3176e6819455c8ba6a963178bc93f512dbd63cd396d1ecf5699bf76e0` |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `f3321778da750ed4a24ce9907af8956dadd6bf022832b1d54594159ef923100b` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `77d4c9cf8917857fd064dc97e41267c199f3483331bf00520a3711b237f84fdc` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2020-03` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9aff667c1b4bcdf7cad32f11cecca0c98a713abe532fe3b05fc126ec06280fd0` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2021-05` | `anomaly` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `31dc1cbbf5971fd5b96174e89bf94dc42d86bc3ddfe80af4a5798045256b520d` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2022-07` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `ba71f1c9474e1b729be5f6ede7a597f1c4f1805d5f9b6ef8b426af49fab92daf` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2022-08` | `gap` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `d48d8deb71deacc0f44066cee209dc54b23a1cb694ea2cbd187c7a106361a522` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `58b6b569c0c109a32f8d1e592aaf64698b287e3e9bd6bdbd3a2a9ab1f7fe0ae0` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2023-02` | `gap` | n/a | 200 | 0 | 648 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `79b89a55307308d21c24d3116eba7a80256a2cf4ec2d91866993479b36a77b48` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2023-04` | `middle` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `8123796c52220fbd26041765f9bb398bd39f6953b3104fddad3d79c32b15786f` |
| `remote` | `index_price_klines` | `ETHUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `df7687e94af210003e030fd710c9841843522a84c6442fe6d536f3487f15c790` |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2020-01` | `first` | n/a | 200 | 0 | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `0014c873b652a617695443046b66f3254a128b0700fe324045ed8e5ac2bc9ee8` |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2020-12` | `gap` | n/a | 200 | 0 | 743 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `01cbc0c45ce59f68dc4151fc3db413303753658468fbc3753b8b153d5b27b4b5` |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2021-06` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `99a950351a0d6c23bb673e20c6ff7c39fc8426ee0718c963bccd331e374945e2` |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `gap` | n/a | 200 | 0 | 624 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `a600a686be980286a511f3eb22eb5f0b88042e56c3e643bfa926e21c17aeb706` |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2022-10` | `gap` | n/a | 200 | 0 | 720 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `c746daaa27bab64d0c65db7309cdf4bd59e214508f0cff0740acd9b3c258ad78` |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2023-04` | `gap,middle` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `46a7e5d131a86bccf157ca10ec0c26579d9ec0025d4a61ad1370bc3b131595d1` |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2026-06` | `gap,latest_complete` | n/a | 200 | 0 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked | `not_available` | `9c5b050a3b928e39ffd1badaefd56c2092751e78e2e6b1c2c03953f58a7c709f` |

## Classified Differences

| Node | Dataset | Symbol | Month | Classification | Open time UTC | Field | ZIP value | REST value | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `high` | `22665.35000000` | `22774.00000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close` | `22646.53000000` | `22681.32000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `volume` | `2830.34558700` | `3685.45440500` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close_time` | `1608559199999` | `1608558440521` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `quote_volume` | `63790349.91077578` | `83180713.81558070` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `trade_count` | `44795` | `62654` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_base_volume` | `1428.55237100` | `1815.00048700` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_quote_volume` | `32189044.97410345` | `40955894.79935769` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `timestamp_mismatch` | `2020-12-21T14:00:00+00:00` | `open_time` | `1608559200000` | `` | ZIP-only timestamp is absent from the selected and adjacent official REST scopes |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `close` | `51080.59000000` | `51048.59000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `volume` | `11667.63216200` | `11815.24808200` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `quote_volume` | `593144862.93087132` | `600681216.08495300` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `trade_count` | `276379` | `279380` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_base_volume` | `5428.08513400` | `5505.78496500` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_quote_volume` | `276430919.50983045` | `280397730.73104759` | official sources contain different canonical values |
| `local` | `um_futures_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `BTCUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `BTCUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2021-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2022-07` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2022-08` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-08` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2020-12` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2021-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `high` | `608.82000000` | `613.29000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close` | `608.31000000` | `610.45000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `volume` | `26146.58875000` | `34927.37209000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close_time` | `1608559199999` | `1608558440528` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `quote_volume` | `15866207.11148880` | `21219132.19507340` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `trade_count` | `14393` | `19857` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_base_volume` | `14284.12764000` | `19843.88555000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_quote_volume` | `8669079.80611710` | `12059602.91269320` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `timestamp_mismatch` | `2020-12-21T14:00:00+00:00` | `open_time` | `1608559200000` | `` | ZIP-only timestamp is absent from the selected and adjacent official REST scopes |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `close` | `2325.82000000` | `2321.44000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `volume` | `187368.61418000` | `188766.41365000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `quote_volume` | `436821371.55040100` | `440066845.48382460` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `trade_count` | `181462` | `182900` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_base_volume` | `84489.57317000` | `85129.16935000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_quote_volume` | `196993734.15928340` | `198479364.97862700` | official sources contain different canonical values |
| `local` | `um_futures_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `ETHUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `ETHUSDT` | `2021-05` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `um_futures_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `ETHUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `ETHUSDT` | `2021-05` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `ETHUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `ETHUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `mark_price_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2021-05` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2022-07` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2022-08` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `index_price_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `ETHUSDT` | `2020-12` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `ETHUSDT` | `2021-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `ETHUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `local` | `premium_index_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | timeout |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2021-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2022-07` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2022-08` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-07` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-08` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2020-12` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2021-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `BTCUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2021-05` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `um_futures_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2021-05` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `mark_price_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2020-03` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2021-05` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2022-07` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2022-08` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2023-02` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `index_price_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2020-01` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2020-12` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2021-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2022-10` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2023-04` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |
| `remote` | `premium_index_klines` | `ETHUSDT` | `2026-06` | `network_blocked` | `n/a` | `source` | `` | `` | url_error_oserror |

## Strict Gate

- Status: blocked
- Blockers:
  - index_price_klines:BTCUSDT:1h:2020-01: network_blocked
  - index_price_klines:BTCUSDT:1h:2020-03: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-04: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-07: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-08: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-10: network_blocked
  - index_price_klines:BTCUSDT:1h:2023-02: network_blocked
  - index_price_klines:BTCUSDT:1h:2023-04: network_blocked
  - index_price_klines:BTCUSDT:1h:2026-06: network_blocked
  - index_price_klines:ETHUSDT:1h:2020-01: network_blocked
  - index_price_klines:ETHUSDT:1h:2020-03: network_blocked
  - index_price_klines:ETHUSDT:1h:2021-05: network_blocked
  - index_price_klines:ETHUSDT:1h:2022-07: network_blocked
  - index_price_klines:ETHUSDT:1h:2022-08: network_blocked
  - index_price_klines:ETHUSDT:1h:2022-10: network_blocked
  - index_price_klines:ETHUSDT:1h:2023-02: network_blocked
  - index_price_klines:ETHUSDT:1h:2023-04: network_blocked
  - index_price_klines:ETHUSDT:1h:2026-06: network_blocked
  - mark_price_klines:BTCUSDT:1h:2020-01: network_blocked
  - mark_price_klines:BTCUSDT:1h:2020-03: network_blocked
  - mark_price_klines:BTCUSDT:1h:2021-06: network_blocked
  - mark_price_klines:BTCUSDT:1h:2021-07: network_blocked
  - mark_price_klines:BTCUSDT:1h:2022-07: network_blocked
  - mark_price_klines:BTCUSDT:1h:2022-08: network_blocked
  - mark_price_klines:BTCUSDT:1h:2022-10: network_blocked
  - mark_price_klines:BTCUSDT:1h:2023-02: network_blocked
  - mark_price_klines:BTCUSDT:1h:2023-04: network_blocked
  - mark_price_klines:BTCUSDT:1h:2026-06: network_blocked
  - mark_price_klines:ETHUSDT:1h:2020-01: network_blocked
  - mark_price_klines:ETHUSDT:1h:2020-03: network_blocked
  - mark_price_klines:ETHUSDT:1h:2021-05: network_blocked
  - mark_price_klines:ETHUSDT:1h:2022-10: network_blocked
  - mark_price_klines:ETHUSDT:1h:2023-02: network_blocked
  - mark_price_klines:ETHUSDT:1h:2023-04: network_blocked
  - mark_price_klines:ETHUSDT:1h:2026-06: network_blocked
  - premium_index_klines:BTCUSDT:1h:2020-01: network_blocked
  - premium_index_klines:BTCUSDT:1h:2020-12: network_blocked
  - premium_index_klines:BTCUSDT:1h:2021-06: network_blocked
  - premium_index_klines:BTCUSDT:1h:2021-07: network_blocked
  - premium_index_klines:BTCUSDT:1h:2022-10: network_blocked
  - premium_index_klines:BTCUSDT:1h:2023-02: network_blocked
  - premium_index_klines:BTCUSDT:1h:2023-04: network_blocked
  - premium_index_klines:BTCUSDT:1h:2026-06: network_blocked
  - premium_index_klines:ETHUSDT:1h:2020-01: network_blocked
  - premium_index_klines:ETHUSDT:1h:2020-12: network_blocked
  - premium_index_klines:ETHUSDT:1h:2021-06: network_blocked
  - premium_index_klines:ETHUSDT:1h:2021-07: network_blocked
  - premium_index_klines:ETHUSDT:1h:2022-10: network_blocked
  - premium_index_klines:ETHUSDT:1h:2023-04: network_blocked
  - premium_index_klines:ETHUSDT:1h:2026-06: network_blocked
  - spot_klines:BTCUSDT:1h:2020-12: source_revision,timestamp_mismatch
  - spot_klines:BTCUSDT:1h:2021-04: source_revision
  - spot_klines:ETHUSDT:1h:2020-12: source_revision,timestamp_mismatch
  - spot_klines:ETHUSDT:1h:2021-04: source_revision
  - um_futures_klines:BTCUSDT:1h:2020-01: network_blocked
  - um_futures_klines:BTCUSDT:1h:2020-03: network_blocked
  - um_futures_klines:BTCUSDT:1h:2021-07: network_blocked
  - um_futures_klines:BTCUSDT:1h:2023-04: network_blocked
  - um_futures_klines:BTCUSDT:1h:2024-10: network_blocked
  - um_futures_klines:BTCUSDT:1h:2026-06: network_blocked
  - um_futures_klines:ETHUSDT:1h:2020-01: network_blocked
  - um_futures_klines:ETHUSDT:1h:2020-03: network_blocked
  - um_futures_klines:ETHUSDT:1h:2021-05: network_blocked
  - um_futures_klines:ETHUSDT:1h:2023-04: network_blocked
  - um_futures_klines:ETHUSDT:1h:2024-10: network_blocked
  - um_futures_klines:ETHUSDT:1h:2026-06: network_blocked

## Decision

- M0 audit status: audit_revalidation_required
- M1A status remains failed_validation.
- M1B status remains failed_validation.
- M2 remains prohibited.
- This report does not approve paper trading, live trading, execution, orders, or API trading permissions.
