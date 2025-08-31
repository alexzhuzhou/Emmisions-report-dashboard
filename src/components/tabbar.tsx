"use client"

import React, { useRef, useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import { IconButton } from '@mui/material';

interface TabBarProps {
  openTabs: string[]
  currentTab: string
  setCurrentTab: any
  setOpenTabs: any
}

const tabbar = ({ openTabs, currentTab, setCurrentTab, setOpenTabs }: TabBarProps) => {

    const router = useRouter();

    const deleteTab = (tab: string) => {
        const idx = openTabs.indexOf(tab);
        const remaining = openTabs.filter((t) => t !== tab);
        setOpenTabs(remaining);

        if (currentTab === tab) {
            let newTab = 'saved';
            if (idx > 0) {
                // Choose the previous tab in the original array
                newTab = openTabs[idx - 1];
            } else if (idx === 0 && remaining.length > 0) {
                newTab = remaining[0];
            }
            setCurrentTab(newTab);
            if (newTab === 'saved') {
                router.push(`/saved`);
            } else {
                router.push(`/saved/${newTab}`);
            }
        }
    };

    
  return (
    <div className='w-full bg-[#C6CBCD] h-[45px] px-[10px] flex items-center gap-[10px] overflow-x-clip'>
        {
            openTabs.map((tab) => {
                let tabName = tab;
                
                let width = Math.trunc(tabName.length * 7 + 70)
                console.log(width)
                
                if (tab == 'saved') {
                    tabName = 'Saved Reports'
                    width = tabName.length * 9
                }

                if (width > 294) {
                    width = 294;
                    if (tab.length > 29) {
                        tabName = tab.substring(0, 29) + '...';
                    }
                }
                
                console.log(width)
                if (tab == currentTab) {
                    return (
                        <div key={tab} className={`h-[33px] flex justify-between items-center bg-[#F5F7FA] rounded-sm px-[9px]`} style={{ width: width }}>
                            <p className='text-[#2F2F2F] text-[13px]'>{tabName}</p>
                            {
                                tab != 'saved' &&
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        deleteTab(tab);
                                    }}
                                    className='cursor-pointer flex justify-center items-center w-[20px] h-[20px] rounded-full hover:bg-[#e5e5e5] transition-all duration-100 ease-in-out'
                                >
                                    <CloseRoundedIcon sx={{ color: "#2F2F2F", fontSize: '16px' }} />
                                </button>
                            }
                        </div>
                    )
                } else {
                    return (
                        <Link key={tab} href={tab == 'saved' ? `/saved` : `/saved/${tab}`}>
                            <div onClick={() => {
                                    setCurrentTab(tab);
                                }} className={`h-[33px] cursor-pointer flex justify-between items-center rounded-sm px-[9px] outline-1 outline-[#979797]`} style={{ width: width }}>
                                <p className='text-[#6D6D6D] text-[13px]'>{tabName}</p>
                                {
                                    tab != 'saved' &&
                                    <button
                                        onClick={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            deleteTab(tab);
                                        }}
                                        className='cursor-pointer flex justify-center items-center w-[20px] h-[20px] rounded-full hover:bg-[#bbbbbb] transition-all duration-100 ease-in-out'
                                    >
                                        <CloseRoundedIcon sx={{ color: "#6D6D6D", fontSize: '16px' }} />
                                    </button>
                                }
                            </div>
                        </Link>
                    )
                }
            })
        }
    </div>
  )
}

export default tabbar