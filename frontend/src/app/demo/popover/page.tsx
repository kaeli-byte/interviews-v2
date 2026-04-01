'use client';
import React from 'react';
import {
    Popover,
    PopoverBody,
    PopoverContent,
    PopoverDescription,
    PopoverHeader,
    PopoverTitle,
    PopoverTrigger,
    PopoverFooter,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { User, Settings, LogOut } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export default function UserProfileDemo() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-8">
            <div className="text-center">
                <h1 className="text-2xl font-bold mb-4">Popover Demo</h1>
                <p className="text-muted-foreground mb-8">Click the avatar to see the user profile popover</p>

                <Popover>
                    <PopoverTrigger asChild>
                        <Button variant="ghost" className="h-12 w-12 rounded-full p-0">
                            <Avatar className="h-10 w-10">
                                <AvatarImage src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=128&h=128&fit=crop&crop=face" />
                                <AvatarFallback>JD</AvatarFallback>
                            </Avatar>
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className='w-72'>
                        <PopoverHeader>
                            <div className="flex items-center space-x-3">
                                <Avatar className="h-10 w-10">
                                    <AvatarImage src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=128&h=128&fit=crop&crop=face" />
                                    <AvatarFallback>JD</AvatarFallback>
                                </Avatar>
                                <div>
                                    <PopoverTitle>John Doe</PopoverTitle>
                                    <PopoverDescription className='text-xs'>john.doe@example.com</PopoverDescription>
                                </div>
                            </div>
                        </PopoverHeader>
                        <PopoverBody className="space-y-1 px-2 py-1">
                            <Button variant="ghost" className="w-full justify-start" size="sm">
                                <User className="mr-2 h-4 w-4" />
                                View Profile
                            </Button>
                            <Button variant="ghost" className="w-full justify-start" size="sm">
                                <Settings className="mr-2 h-4 w-4" />
                                Settings
                            </Button>
                        </PopoverBody>
                        <PopoverFooter>
                            <Button variant="outline" className="w-full bg-transparent" size="sm">
                                <LogOut className="mr-2 h-4 w-4" />
                                Sign Out
                            </Button>
                        </PopoverFooter>
                    </PopoverContent>
                </Popover>
            </div>
        </div>
    );
}